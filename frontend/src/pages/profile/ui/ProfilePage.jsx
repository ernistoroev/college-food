import { useRef, useState } from 'react';
import { Camera, UserRound, X } from 'lucide-react';

export default function ProfilePage({ currentUser, onSave, onClose, onLogout }) {
  const [name, setName] = useState(currentUser?.name || '');
  const [course, setCourse] = useState(currentUser?.course || '');
  const [faculty, setFaculty] = useState(currentUser?.faculty || '');
  const [avatar, setAvatar] = useState(currentUser?.avatar || '');
  const [avatarFile, setAvatarFile] = useState(null);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const fileInput = useRef(null);

  function handleAvatarChange(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setError('Выбери файл изображения.');
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      setError('Изображение должно быть не больше 2 МБ.');
      return;
    }

    // The file goes to the server on save; here it is only read for the preview.
    const reader = new FileReader();
    reader.onload = () => {
      setAvatar(String(reader.result));
      setAvatarFile(file);
      setError('');
    };
    reader.onerror = () => setError('Не удалось загрузить изображение.');
    reader.readAsDataURL(file);
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (name.trim().length < 2) {
      setError('Имя должно содержать минимум 2 символа.');
      return;
    }

    setSaving(true);
    const saveError = await onSave({
      name: name.trim(),
      course: course.trim(),
      faculty: faculty.trim(),
      avatarFile
    });
    setSaving(false);
    if (saveError) setError(saveError);
  }

  return (
    <div
      onMouseDown={event => {
        if (event.target === event.currentTarget) onClose();
      }}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 1200,
        background: 'rgba(0,0,0,.48)',
        display: 'grid',
        placeItems: 'center',
        padding: 16,
        overflowY: 'auto'
      }}
    >
      <section
        style={{
          width: '100%',
          maxWidth: 520,
          maxHeight: '92vh',
          overflowY: 'auto',
          background: '#ffffff',
          color: '#202020',
          borderRadius: 22,
          padding: 28,
          position: 'relative',
          boxShadow: '0 20px 70px rgba(0,0,0,.2)'
        }}
      >
        <button
          type="button"
          onClick={onClose}
          aria-label="Закрыть профиль"
          style={{
            position: 'absolute',
            right: 18,
            top: 18,
            border: 0,
            background: '#f3f3f3',
            borderRadius: 10,
            width: 38,
            height: 38,
            cursor: 'pointer'
          }}
        >
          <X size={19} />
        </button>

        <span style={{ color: '#e9483b', fontSize: 12, fontWeight: 700 }}>
          COLLEGE FOOD
        </span>
        <h1 style={{ fontSize: 30, margin: '8px 0', color: '#202020', lineHeight: 1.2, letterSpacing: '-0.8px' }}>Личный кабинет</h1>
        <p style={{ color: '#666666', marginTop: 0, lineHeight: 1.6 }}>
          Информация о твоём студенческом профиле.
        </p>

        <form onSubmit={handleSubmit}>
          <div style={{ textAlign: 'center', margin: '24px 0' }}>
            <div
              style={{
                width: 112,
                height: 112,
                margin: '0 auto 12px',
                borderRadius: '50%',
                overflow: 'hidden',
                background: '#f2f2f2',
                display: 'grid',
                placeItems: 'center'
              }}
            >
              {avatar ? (
                <img
                  src={avatar}
                  alt="Аватар профиля"
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              ) : (
                <UserRound size={48} color="#999" />
              )}
            </div>

            <button
              type="button"
              onClick={() => fileInput.current?.click()}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                padding: '10px 14px',
                border: '1px solid #ddd',
                borderRadius: 10,
                background: '#fff',
                cursor: 'pointer'
              }}
            >
              <Camera size={17} />
              Изменить аватар
            </button>

            <input
              ref={fileInput}
              type="file"
              accept="image/*"
              onChange={handleAvatarChange}
              style={{ display: 'none' }}
            />
          </div>

          <label style={{ display: 'block', marginBottom: 16, fontWeight: 600 }}>
            Имя
            <input
              value={name}
              onChange={event => setName(event.target.value)}
              required
              minLength={2}
              maxLength={80}
              placeholder="Твоё имя"
              style={inputStyle}
            />
          </label>

          <label style={{ display: 'block', marginBottom: 16, fontWeight: 600 }}>
            Курс
            <input
              value={course}
              onChange={event => setCourse(event.target.value)}
              maxLength={80}
              placeholder="Например, 2 курс"
              style={inputStyle}
            />
          </label>

          <label style={{ display: 'block', marginBottom: 18, fontWeight: 600 }}>
            Факультет
            <input
              value={faculty}
              onChange={event => setFaculty(event.target.value)}
              maxLength={120}
              placeholder="Например, IT"
              style={inputStyle}
            />
          </label>

          {error && (
            <p style={{ color: '#c62828', fontSize: 14 }}>{error}</p>
          )}

          <button
            type="submit"
            disabled={saving}
            style={{
              width: '100%',
              border: 0,
              borderRadius: 12,
              padding: 15,
              background: '#e9483b',
              color: '#ffffff',
              fontWeight: 700,
              fontSize: 15,
              cursor: 'pointer'
            }}
          >
            {saving ? 'Сохраняем…' : 'Сохранить изменения'}
          </button>
        </form>

        <button
          type="button"
          onClick={onLogout}
          style={{
            width: '100%',
            marginTop: 12,
            border: '1px solid #ddd',
            borderRadius: 12,
            padding: 13,
            background: '#ffffff',
            color: '#202020',
            fontWeight: 600,
            fontSize: 14,
            cursor: 'pointer'
          }}
        >
          Выйти из аккаунта
        </button>

        <p style={{ color: '#666666', fontSize: 12, lineHeight: 1.6, marginBottom: 0 }}>
          {currentUser?.email}
        </p>
      </section>
    </div>
  );
}

const inputStyle = {
  display: 'block',
  boxSizing: 'border-box',
  width: '100%',
  marginTop: 8,
  padding: '13px 14px',
  border: '1px solid #d9d9d9',
  borderRadius: 10,
  background: '#ffffff',
  color: '#202020',
  fontSize: 15,
  outlineColor: '#e9483b'
};
