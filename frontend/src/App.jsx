import { useState, useEffect } from 'react';
import {
  ShoppingCart,
  Utensils,
  X,
  Minus,
  Plus,
  Trash2,
  ClipboardList,
  Clock,
  CheckCircle2,
  Package
} from 'lucide-react';

import { QRCodeSVG } from 'qrcode.react';
import './App.css';
import { fetchMenu, ALL_CATEGORIES } from './entities/dish/api/dishes.js';
import MenuPage from './pages/menu/ui/MenuPage.jsx';
import { getErrorMessage } from './shared/api/client.js';

import {
  addItemToCart,
  removeItemFromCart,
  deleteItemFromCart,
  getCartCount,
  getCartTotal
} from './entities/cart/model/cart.js';

import { fetchOrders, createOrder } from './entities/order/model/orders.js';

import CheckoutForm from './features/checkout/ui/CheckoutForm.jsx';
import ReviewsPage from './pages/reviews/ui/ReviewsPage.jsx';
import AuthModal from './features/auth/ui/AuthModal.jsx';
import ProfilePage from './pages/profile/ui/ProfilePage.jsx';
import { fetchCurrentUser, logout, updateProfile } from './entities/auth/model/auth.js';

export default function App() {
  const [category, setCategory] = useState(ALL_CATEGORIES);
  const [menuDishes, setMenuDishes] = useState([]);
  const [categories, setCategories] = useState([ALL_CATEGORIES]);
  const [menuLoading, setMenuLoading] = useState(true);
  const [menuError, setMenuError] = useState('');
  const [search, setSearch] = useState('');
  const [cart, setCart] = useState([]);
  const [cartOpen, setCartOpen] = useState(false);
  const [checkoutOpen, setCheckoutOpen] = useState(false);
  const [orders, setOrders] = useState([]);
  const [ordersOpen, setOrdersOpen] = useState(false);
  const [reviewsOpen, setReviewsOpen] = useState(false);
  const [authOpen, setAuthOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [paymentOrder, setPaymentOrder] = useState(null);
  const [paymentSeconds, setPaymentSeconds] = useState(30);
  const [paymentExpired, setPaymentExpired] = useState(false);
  const [paying, setPaying] = useState(false);

  const cartCount = getCartCount(cart);
  const cartTotal = getCartTotal(cart);

  const filtered = menuDishes.filter(
    dish =>
      (category === ALL_CATEGORIES || dish.category === category) &&
      dish.name.toLowerCase().includes(search.toLowerCase())
  );

  // Menu and categories come from the backend; portions left (stock) are counted there too.
  function loadMenu() {
    return fetchMenu()
      .then(menu => {
        setMenuDishes(menu.dishes);
        setCategories(menu.categories);
        setMenuError('');
      })
      .catch(error => setMenuError(getErrorMessage(error)))
      .finally(() => setMenuLoading(false));
  }

  // Called on login and logout: «Мои заказы» belong to the logged-in student.
  function changeUser(user) {
    setCurrentUser(user);
    if (!user) {
      setOrders([]);
      return;
    }

    fetchOrders()
      .then(setOrders)
      .catch(() => setOrders([]));
  }

  useEffect(() => {
    loadMenu();
    // If a token from the last visit still works, the student stays logged in.
    fetchCurrentUser().then(changeUser);
  }, []);

  useEffect(() => {
    function handleEscape(event) {
      if (event.key === 'Escape') {
        setCheckoutOpen(false);
        setCartOpen(false);
      }
    }

    if (cartOpen || checkoutOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [cartOpen, checkoutOpen]);


  useEffect(() => {
    if (!paymentOrder || paymentExpired) return;

    if (paymentSeconds <= 0) {
      setPaymentExpired(true);
      return;
    }

    const timer = setTimeout(() => {
      setPaymentSeconds(seconds => seconds - 1);
    }, 1000);

    return () => clearTimeout(timer);
  }, [paymentOrder, paymentSeconds, paymentExpired]);

  function addToCart(dish) {
    const currentDish = menuDishes.find(
      item => item.id === dish.id
    );

    if (!currentDish || currentDish.stock <= 0) return;

    setMenuDishes(old =>
      old.map(item =>
        item.id === dish.id
          ? { ...item, stock: item.stock - 1 }
          : item
      )
    );

    setCart(old => addItemToCart(old, currentDish));
  }

  function removeFromCart(dish) {
    const cartItem = cart.find(item => item.id === dish.id);

    if (!cartItem) return;

    setCart(old => removeItemFromCart(old, dish.id));

    setMenuDishes(old =>
      old.map(item =>
        item.id === dish.id
          ? { ...item, stock: item.stock + 1 }
          : item
      )
    );
  }

  function deleteFromCart(dish) {
    const cartItem = cart.find(item => item.id === dish.id);

    if (!cartItem) return;

    setMenuDishes(old =>
      old.map(item =>
        item.id === dish.id
          ? { ...item, stock: item.stock + cartItem.quantity }
          : item
      )
    );

    setCart(old => deleteItemFromCart(old, dish.id));
  }

  function handleCheckout(orderData) {
    if (cart.length === 0) return;

    const order = {
      id: Date.now(),
      ...orderData,
      items: cart.map(item => ({ ...item })),
      total: cartTotal,
      createdAt: new Date().toLocaleString('ru-RU'),
      status: 'Ожидает оплаты',
    };

    setPaymentOrder(order);
    setPaymentSeconds(30);
    setPaymentExpired(false);
    setCheckoutOpen(false);
  }

  // The payment is a demo; the order itself is saved on the server after «Я оплатил».
  async function finishPaymentDemo() {
    if (!paymentOrder || paymentExpired || paying) return;

    setPaying(true);
    try {
      const order = await createOrder(paymentOrder);
      setOrders(old => [order, ...old]);
      setCart([]);
      setPaymentOrder(null);
      setCartOpen(false);
      setCheckoutOpen(false);
      setOrdersOpen(true);
      setReviewsOpen(false);
      loadMenu();
    } catch (error) {
      window.alert(getErrorMessage(error, 'Не удалось оформить заказ.'));
    } finally {
      setPaying(false);
    }
  }

  // Returns an error text for the profile form, or null if everything is saved.
  async function handleProfileSave(profile) {
    try {
      const user = await updateProfile(profile);
      setCurrentUser(user);
      setProfileOpen(false);
      return null;
    } catch (error) {
      return getErrorMessage(error, 'Не удалось сохранить профиль.');
    }
  }

  async function handleLogout() {
    await logout().catch(() => {});
    changeUser(null);
    setProfileOpen(false);
    setOrdersOpen(false);
  }

  function showMenu() {
    setOrdersOpen(false);
    setReviewsOpen(false);
  }

  function showOrders() {
    if (!currentUser) {
      setAuthOpen(true);
      return;
    }
    setOrdersOpen(true);
    setReviewsOpen(false);
  }

  function showReviews() {
    setOrdersOpen(false);
    setReviewsOpen(true);
  }

  return (
    <div className="app" style={{display: 'flex', flexDirection: 'column', minHeight: '100vh'}}>
      <header className="header">
        <a
          href="#menu"
          className="logo"
          onClick={showMenu}
        >
          <span className="logo-icon">
            <Utensils />
          </span>

          <span>
            COLLEGE <b>FOOD</b>
            <small>СТУДЕНЧЕСКАЯ СТОЛОВАЯ</small>
          </span>
        </a>

        <nav>
          <a
            className={!ordersOpen && !reviewsOpen ? 'active' : ''}
            href="#menu"
            onClick={showMenu}
          >
            Меню
          </a>

          <a
            className={ordersOpen && !reviewsOpen ? 'active' : ''}
            href="#orders"
            onClick={showOrders}
          >
            Мои заказы
          </a>



          <a
            className={reviewsOpen ? 'active' : ''}
            href="#reviews"
            onClick={showReviews}
          >
            Отзывы
          </a>

          <a href="#contacts">
            Контакты
          </a>
        </nav>

        <div className="header-actions">
          <button
            type="button"
            className="login-button"
            onClick={() => {
              if (currentUser) {
                setProfileOpen(true);
              } else {
                setAuthOpen(true);
              }
            }}
          >
            {currentUser ? currentUser.name : 'Войти'}
          </button>

          <button
            type="button"
            className="cart-button"
            onClick={() => setCartOpen(true)}
          >
            <ShoppingCart size={18} />
            Корзина
            {cartCount > 0 && <b>{cartCount}</b>}
          </button>
        </div>
      </header>

      <main style={{flex: '1'}}>
        {reviewsOpen ? (
          <ReviewsPage
            currentUser={currentUser}
            onLogin={() => setAuthOpen(true)}
          />
        ) : ordersOpen ? (
          <section
            id="orders"
            style={{
              maxWidth: 1180,
              margin: '0 auto',
              padding: '48px 24px 72px',
              minHeight: '60vh'
            }}
          >
            <div style={{ marginBottom: 32 }}>
              <span className="eyebrow">COLLEGE FOOD</span>

              <h1
                style={{
                  margin: '10px 0',
                  fontSize: 'clamp(30px, 4vw, 44px)',
                  color: 'var(--text-primary, #222)',
                  letterSpacing: '-1px'
                }}
              >
                Мои заказы
              </h1>

              <p style={{ color: 'var(--text-secondary, #777)' }}>
                Здесь хранится история твоих заказов.
              </p>
            </div>

            {orders.length === 0 ? (
              <div
                style={{
                  padding: '48px 20px',
                  textAlign: 'center',
                  border: '1px solid #e9e9e9',
                  borderRadius: 20,
                  background: 'var(--card-bg, #fff)'
                }}
              >
                <ClipboardList
                  size={44}
                  color="#e9483b"
                  style={{ marginBottom: 12 }}
                />

                <h2 style={{ color: 'var(--text-primary, #222)' }}>
                  Заказов пока нет
                </h2>

                <p style={{ color: 'var(--text-secondary, #777)' }}>
                  Выбери блюда в меню и оформи первый заказ.
                </p>

                <button
                  type="button"
                  className="checkout-button"
                  style={{ marginTop: 16, maxWidth: 240 }}
                  onClick={showMenu}
                >
                  Перейти в меню
                </button>
              </div>
            ) : (
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 320px), 1fr))',
                  gap: 20
                }}
              >
                {orders.map(order => (
                  <article
                    key={order.id}
                    style={{
                      padding: 24,
                      border: '1px solid #e9e9e9',
                      borderRadius: 20,
                      background: 'var(--card-bg, #fff)',
                      boxShadow: '0 5px 20px rgba(0,0,0,0.035)',
                      minWidth: 0
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        justifyContent: 'space-between',
                        gap: 12,
                        marginBottom: 18
                      }}
                    >
                      <div>
                        <span
                          style={{
                            color: 'var(--text-secondary, #777)',
                            fontSize: 12
                          }}
                        >
                          НОМЕР ЗАКАЗА
                        </span>

                        <h2
                          style={{
                            margin: '5px 0 0',
                            fontSize: 21,
                            color: 'var(--text-primary, #222)',
                            overflowWrap: 'anywhere'
                          }}
                        >
                          №{order.id}
                        </h2>
                      </div>

                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 6,
                          padding: '8px 10px',
                          borderRadius: 30,
                          background: '#eaf7ed',
                          color: '#237a3b',
                          fontSize: 12,
                          fontWeight: 700,
                          whiteSpace: 'nowrap'
                        }}
                      >
                        <CheckCircle2 size={14} />
                        {order.status}
                      </span>
                    </div>

                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        color: 'var(--text-secondary, #777)',
                        fontSize: 13,
                        marginBottom: 8
                      }}
                    >
                      <Clock size={15} />
                      <span>{order.createdAt}</span>
                    </div>

                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        color: 'var(--text-secondary, #777)',
                        fontSize: 13,
                        marginBottom: 20
                      }}
                    >
                      <Package size={15} />
                      Получение: {order.pickupTime}
                    </div>

                    <div
                      style={{
                        borderTop: '1px solid #eeeeee',
                        borderBottom: '1px solid #eeeeee',
                        padding: '16px 0',
                        marginBottom: 16
                      }}
                    >
                      <h3
                        style={{
                          fontSize: 14,
                          margin: '0 0 12px',
                          color: 'var(--text-primary, #222)'
                        }}
                      >
                        Состав заказа
                      </h3>

                      {order.items?.map((item, index) => (
                        <div
                          key={`${item.id}-${index}`}
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            gap: 12,
                            marginTop: 10,
                            fontSize: 14,
                            color: 'var(--text-secondary, #666)'
                          }}
                        >
                          <span style={{ overflowWrap: 'anywhere' }}>
                            {item.name} × {item.quantity}
                          </span>

                          <strong
                            style={{
                              color: 'var(--text-primary, #222)',
                              whiteSpace: 'nowrap'
                            }}
                          >
                            {item.price * item.quantity} сом
                          </strong>
                        </div>
                      ))}
                    </div>

                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        gap: 12
                      }}
                    >
                      <span style={{ color: 'var(--text-secondary, #777)' }}>
                        Итого
                      </span>

                      <strong
                        style={{
                          fontSize: 22,
                          color: '#e9483b',
                          whiteSpace: 'nowrap'
                        }}
                      >
                        {order.total} сом
                      </strong>
                    </div>

                    <p
                      style={{
                        margin: '14px 0 0',
                        fontSize: 13,
                        color: 'var(--text-secondary, #777)'
                      }}
                    >
                      Получатель: {order.studentName}
                    </p>
                  </article>
                ))}
              </div>
            )}

            <button
              type="button"
              className="checkout-cancel"
              style={{ marginTop: 24, width: 'auto' }}
              onClick={showMenu}
            >
              Вернуться в меню
            </button>
          </section>
        ) : (
          <MenuPage
            category={category}
            setCategory={setCategory}
            categories={categories}
            search={search}
            setSearch={setSearch}
            filtered={filtered}
            addToCart={addToCart}
            loading={menuLoading}
            error={menuError}
          />
        )}
      </main>

      <footer id="contacts">
        <b>COLLEGE <em>FOOD</em></b>
        <span>Вкусная еда для больших идей.</span>
        <small>Пн–Пт · 08:00–16:00 · © 2026 College Food</small>
      </footer>

      {cartOpen && (
        <div
          className="cart-overlay"
          onMouseDown={event => {
            if (event.target === event.currentTarget) {
              setCartOpen(false);
            }
          }}
        >
          <section
            className="cart-panel"
            role="dialog"
            aria-modal="true"
            aria-labelledby="cart-title"
          >
            <div className="cart-heading">
              <div>
                <span className="eyebrow">COLLEGE FOOD</span>
                <h2 id="cart-title">
                  Корзина <small>({cartCount})</small>
                </h2>
              </div>

              <button
                type="button"
                className="cart-close"
                onClick={() => setCartOpen(false)}
                aria-label="Закрыть корзину"
              >
                <X size={20} />
              </button>
            </div>

            {cart.length === 0 ? (
              <div className="cart-empty">
                <ShoppingCart size={42} />
                <h3>Корзина пока пустая</h3>
                <p>Добавь любимые блюда из меню.</p>

                <button
                  type="button"
                  className="checkout-button"
                  onClick={() => setCartOpen(false)}
                >
                  Вернуться к меню
                </button>
              </div>
            ) : (
              <>
                <div className="cart-items">
                  {cart.map(item => (
                    <article className="cart-item" key={item.id}>
                      {item.image ? (
                        <img src={item.image} alt={item.name} />
                      ) : (
                        <div className="cart-item-no-photo"><Utensils size={24} /></div>
                      )}

                      <div className="cart-item-info">
                        <h3>{item.name}</h3>

                        <strong>
                          {item.price * item.quantity} сом
                        </strong>

                        <p>{item.price} сом за порцию</p>

                        <div className="quantity-control">
                          <button
                            type="button"
                            onClick={() => removeFromCart(item)}
                            aria-label="Уменьшить количество"
                          >
                            <Minus size={15} />
                          </button>

                          <span>{item.quantity}</span>

                          <button
                            type="button"
                            onClick={() => addToCart(item)}
                            disabled={
                              menuDishes.find(
                                dish => dish.id === item.id
                              )?.stock === 0
                            }
                            aria-label="Увеличить количество"
                          >
                            <Plus size={15} />
                          </button>

                          <button
                            type="button"
                            className="remove-item"
                            onClick={() => deleteFromCart(item)}
                            aria-label="Удалить блюдо"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>

                <div className="cart-summary">
                  <div>
                    <span>Количество порций</span>
                    <span>{cartCount}</span>
                  </div>

                  <div className="cart-total">
                    <span>Итого</span>
                    <strong>{cartTotal} сом</strong>
                  </div>

                  <button
                    type="button"
                    className="checkout-button"
                    onClick={() => {
                      setCartOpen(false);
                      // Orders are saved for an account, so the student has to log in first.
                      if (currentUser) {
                        setCheckoutOpen(true);
                      } else {
                        setAuthOpen(true);
                      }
                    }}
                  >
                    Оформить заказ
                  </button>

                  <p className="cart-note">
                    Проверь состав заказа перед подтверждением.
                  </p>
                </div>
              </>
            )}
          </section>
        </div>
      )}

      {profileOpen && currentUser && (
        <ProfilePage
          currentUser={currentUser}
          onSave={handleProfileSave}
          onClose={() => setProfileOpen(false)}
          onLogout={handleLogout}
        />
      )}

      {authOpen && (
        <AuthModal
          onClose={() => setAuthOpen(false)}
          onLogin={changeUser}
        />
      )}

      {checkoutOpen && (
        <div
          className="cart-overlay"
          onMouseDown={event => {
            if (event.target === event.currentTarget) {
              setCheckoutOpen(false);
            }
          }}
        >
          <section
            className="cart-panel"
            role="dialog"
            aria-modal="true"
            aria-label="Оформление заказа"
          >
            <button
              type="button"
              className="cart-close"
              onClick={() => setCheckoutOpen(false)}
              aria-label="Закрыть оформление заказа"
            >
              <X size={20} />
            </button>

            <CheckoutForm
              cart={cart}
              cartTotal={cartTotal}
              currentUser={currentUser}
              onSubmit={handleCheckout}
              onCancel={() => setCheckoutOpen(false)}
            />
          </section>
        </div>
      )}

      {paymentOrder && (
        <div className="cart-overlay">
          <section
            className="cart-panel payment-panel"
            role="dialog"
            aria-modal="true"
            aria-label="Оплата заказа"
          >
            <button
              type="button"
              className="cart-close"
              onClick={() => setPaymentOrder(null)}
              aria-label="Закрыть оплату"
            >
              <X size={20} />
            </button>

            {paymentExpired ? (
              <div className="payment-result">
                <Clock size={44} color="#e9483b" />
                <h2>Время истекло</h2>
                <p>Время демонстрационной оплаты закончилось.</p>
                <button
                  type="button"
                  className="checkout-button"
                  onClick={() => {
                    setPaymentSeconds(30);
                    setPaymentExpired(false);
                  }}
                >
                  Попробовать снова
                </button>
                <button
                  type="button"
                  className="checkout-cancel"
                  onClick={() => setPaymentOrder(null)}
                >
                  Закрыть
                </button>
              </div>
            ) : (
              <>
                <span className="eyebrow">COLLEGE FOOD</span>
                <h2>Оплата заказа</h2>
                <p>Заказ №{paymentOrder.id}</p>

                <div className="payment-qr">
                  <QRCodeSVG
                    value={`COLLEGE-FOOD-DEMO-${paymentOrder.id}-${paymentOrder.total}`}
                    size={200}
                    level="M"
                    includeMargin
                  />
                </div>

                <p className="payment-hint">
                  Отсканируй QR-код камерой телефона.
                </p>

                <div className="payment-total">
                  <span>К оплате</span>
                  <strong>{paymentOrder.total} сом</strong>
                </div>

                <div
                  className="payment-timer"
                  style={{
                    '--timer-progress': `${(paymentSeconds / 30) * 100}%`,
                  }}
                >
                  <div className="payment-timer-ring">
                    <strong>
                      00:{String(paymentSeconds).padStart(2, '0')}
                    </strong>
                    <span>до окончания</span>
                  </div>
                </div>

                <button
                  type="button"
                  className="checkout-button"
                  onClick={finishPaymentDemo}
                  disabled={paying}
                >
                  {paying ? 'Сохраняем заказ…' : 'Я оплатил'}
                </button>

                <p className="payment-disclaimer">
                  Деморежим: QR-код не принимает реальные платежи.
                </p>
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
