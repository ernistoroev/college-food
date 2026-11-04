import { useCallback, useEffect, useState } from 'react';
import { api, getList, getErrorMessage } from '../../../shared/api/client.js';

const emptyForm = {
  name: '',
  description: '',
  price: '',
  category: '',
  weight: '0',
  weight_unit: 'г',
  portions_today: '0',
  is_available: true,
  image: null,
};

export default function AdminDishesPage() {
  const [dishes, setDishes] = useState([]);
  const [categories, setCategories] = useState([]);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [updating, setUpdating] = useState(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [editingDish, setEditingDish] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');

  const loadDishes = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      const params = {};
      if (search.trim()) params.search = search.trim();
      if (category !== 'all') params.category = category;

      const [dishData, categoryData] = await Promise.all([
        getList('/dishes/', params),
        getList('/categories/'),
      ]);

      setDishes(dishData);
      setCategories(categoryData);
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'Не удалось загрузить меню.'));
    } finally {
      setLoading(false);
    }
  }, [search, category]);

  useEffect(() => {
    const timer = setTimeout(loadDishes, 250);
    return () => clearTimeout(timer);
  }, [loadDishes]);

  function openCreateModal() {
    setEditingDish(null);
    setForm({
      ...emptyForm,
      category: categories[0] ? String(categories[0].id) : '',
    });
    setFormError('');
    setModalOpen(true);
  }

  function openEditModal(dish) {
    setEditingDish(dish);
    setForm({
      name: dish.name || '',
      description: dish.description || '',
      price: dish.price ?? '',
      category: String(dish.category ?? ''),
      weight: String(dish.weight ?? 0),
      weight_unit: dish.weight_unit || 'г',
      portions_today: String(dish.portions_today ?? 0),
      is_available: Boolean(dish.is_available),
      image: null,
    });
    setFormError('');
    setModalOpen(true);
  }

  function updateField(event) {
    const { name, value, type, checked, files } = event.target;

    setForm(current => ({
      ...current,
      [name]: type === 'checkbox'
        ? checked
        : type === 'file'
          ? files?.[0] || null
          : value,
    }));
  }

  async function saveDish(event) {
    event.preventDefault();
    setFormError('');

    if (!form.name.trim() || !form.category || form.price === '') {
      setFormError('Заполните название, категорию и цену.');
      return;
    }

    if (Number(form.price) < 0 || Number(form.weight) < 0 || Number(form.portions_today) < 0) {
      setFormError('Числовые значения не могут быть отрицательными.');
      return;
    }

    if (form.image && form.image.size > 5 * 1024 * 1024) {
      setFormError('Фотография должна быть не больше 5 МБ.');
      return;
    }

    const data = new FormData();
    data.append('name', form.name.trim());
    data.append('description', form.description);
    data.append('price', form.price);
    data.append('category', form.category);
    data.append('weight', form.weight || '0');
    data.append('weight_unit', form.weight_unit);
    data.append('portions_today', form.portions_today || '0');
    data.append('is_available', String(form.is_available));

    if (form.image) data.append('image', form.image);

    setSaving(true);

    try {
      if (editingDish) {
        await api.patch(`/dishes/${editingDish.id}/`, data);
      } else {
        await api.post('/dishes/', data);
      }

      setModalOpen(false);
      await loadDishes();
    } catch (requestError) {
      setFormError(getErrorMessage(requestError, 'Не удалось сохранить блюдо.'));
    } finally {
      setSaving(false);
    }
  }

  async function deleteDish(dish) {
    const confirmed = window.confirm(
      `Удалить блюдо «${dish.name}»? Это действие нельзя отменить.`
    );

    if (!confirmed) return;

    setUpdating(dish.id);
    setError('');

    try {
      await api.delete(`/dishes/${dish.id}/`);
      setDishes(current => current.filter(item => item.id !== dish.id));
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'Не удалось удалить блюдо.'));
    } finally {
      setUpdating(null);
    }
  }

  async function toggleAvailability(dish) {
    setUpdating(dish.id);
    setError('');

    try {
      const response = await api.patch(
        `/dishes/${dish.id}/availability/`,
        { is_available: !dish.is_available }
      );

      setDishes(current =>
        current.map(item => item.id === dish.id ? response.data : item)
      );
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'Не удалось изменить доступность.'));
    } finally {
      setUpdating(null);
    }
  }

  function formatPrice(value) {
    return `${Number(value || 0).toLocaleString('ru-RU')} сом`;
  }

  return (
    <div className="admin-dishes">
      <div className="admin-page-heading">
        <div>
          <span className="admin-eyebrow">COLLEGE FOOD / УПРАВЛЕНИЕ</span>
          <h1>Блюда</h1>
          <p>Управление ассортиментом и наличием порций.</p>
        </div>

        <div className="admin-dishes-heading-actions">
          <button className="admin-refresh" onClick={loadDishes} disabled={loading}>
            ↻ Обновить
          </button>
          <button className="admin-add-dish" onClick={openCreateModal}>
            + Добавить блюдо
          </button>
        </div>
      </div>

      <div className="admin-dishes-toolbar">
        <input
          type="search"
          placeholder="Поиск по названию блюда..."
          value={search}
          onChange={event => setSearch(event.target.value)}
        />

        <select value={category} onChange={event => setCategory(event.target.value)}>
          <option value="all">Все категории</option>
          {categories.map(item => (
            <option key={item.id} value={item.id}>{item.name}</option>
          ))}
        </select>
      </div>

      {error && <div className="admin-orders-error">{error}</div>}

      {loading ? (
        <div className="admin-orders-empty">Загружаем меню...</div>
      ) : dishes.length === 0 ? (
        <div className="admin-orders-empty">
          <span>♨</span>
          <h3>Блюда не найдены</h3>
          <p>Попробуйте изменить поисковый запрос или добавить блюдо.</p>
        </div>
      ) : (
        <div className="admin-dishes-grid">
          {dishes.map(dish => (
            <article className="admin-dish-card" key={dish.id}>
              {dish.image ? (
                <img src={dish.image} alt={dish.name} className="admin-dish-image" />
              ) : (
                <div className="admin-dish-image admin-dish-no-image">♨</div>
              )}

              <div className="admin-dish-content">
                <span className="admin-dish-category">
                  {dish.category_name || 'Без категории'}
                </span>

                <h3>{dish.name}</h3>
                <p className="admin-dish-description">
                  {dish.description || 'Описание отсутствует'}
                </p>

                <div className="admin-dish-info">
                  <strong>{formatPrice(dish.price)}</strong>
                  <span>
                    {dish.weight ? `${dish.weight} ${dish.weight_unit || 'г'}` : 'Вес не указан'}
                  </span>
                </div>

                <div className="admin-dish-stock">
                  <span>Порций сегодня</span>
                  <strong>{dish.portions_today}</strong>
                </div>

                <div className="admin-dish-status">
                  <span className={dish.is_available ? 'available' : 'unavailable'}>
                    {dish.is_available ? 'Доступно' : 'Отключено'}
                  </span>

                  <button
                    className={`admin-dish-toggle ${dish.is_available ? 'is-on' : ''}`}
                    onClick={() => toggleAvailability(dish)}
                    disabled={updating === dish.id}
                  >
                    {updating === dish.id ? '...' : dish.is_available ? 'Отключить' : 'Включить'}
                  </button>
                </div>

                <div className="admin-dish-actions">
                  <button onClick={() => openEditModal(dish)}>Редактировать</button>
                  <button
                    className="admin-dish-delete"
                    onClick={() => deleteDish(dish)}
                    disabled={updating === dish.id}
                  >
                    Удалить
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      {modalOpen && (
        <div className="admin-dish-modal-backdrop" onClick={() => !saving && setModalOpen(false)}>
          <section
            className="admin-dish-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="admin-dish-modal-title"
            onClick={event => event.stopPropagation()}
          >
            <div className="admin-dish-modal-heading">
              <div>
                <span className="admin-eyebrow">COLLEGE FOOD / МЕНЮ</span>
                <h2 id="admin-dish-modal-title">
                  {editingDish ? 'Редактировать блюдо' : 'Новое блюдо'}
                </h2>
              </div>
              <button
                type="button"
                className="admin-dish-modal-close"
                onClick={() => setModalOpen(false)}
                disabled={saving}
              >
                ×
              </button>
            </div>

            <form className="admin-dish-form" onSubmit={saveDish}>
              <label>
                Название блюда *
                <input name="name" value={form.name} onChange={updateField} required maxLength={200} />
              </label>

              <label>
                Категория *
                <select name="category" value={form.category} onChange={updateField} required>
                  <option value="">Выберите категорию</option>
                  {categories.map(item => (
                    <option key={item.id} value={item.id}>{item.name}</option>
                  ))}
                </select>
              </label>

              <label>
                Описание
                <textarea name="description" value={form.description} onChange={updateField} rows={3} />
              </label>

              <div className="admin-dish-form-row">
                <label>
                  Цена, сом *
                  <input name="price" type="number" min="0" step="0.01" value={form.price} onChange={updateField} required />
                </label>

                <label>
                  Количество порций
                  <input name="portions_today" type="number" min="0" step="1" value={form.portions_today} onChange={updateField} />
                </label>
              </div>

              <div className="admin-dish-form-row">
                <label>
                  Вес / объём
                  <input name="weight" type="number" min="0" step="1" value={form.weight} onChange={updateField} />
                </label>

                <label>
                  Единица измерения
                  <select name="weight_unit" value={form.weight_unit} onChange={updateField}>
                    <option value="г">Граммы (г)</option>
                    <option value="мл">Миллилитры (мл)</option>
                  </select>
                </label>
              </div>

              <label>
                Фотография блюда (до 5 МБ)
                <input name="image" type="file" accept="image/*" onChange={updateField} />
              </label>

              {form.image && (
                <p className="admin-dish-file-name">Выбрано: {form.image.name}</p>
              )}

              <label className="admin-dish-checkbox">
                <input
                  type="checkbox"
                  name="is_available"
                  checked={form.is_available}
                  onChange={updateField}
                />
                Блюдо доступно для заказа
              </label>

              {formError && <div className="admin-orders-error">{formError}</div>}

              <div className="admin-dish-form-actions">
                <button type="button" onClick={() => setModalOpen(false)} disabled={saving}>
                  Отмена
                </button>
                <button type="submit" disabled={saving}>
                  {saving ? 'Сохраняем...' : editingDish ? 'Сохранить изменения' : 'Добавить блюдо'}
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
    </div>
  );
}
