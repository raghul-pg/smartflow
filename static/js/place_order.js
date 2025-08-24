// static/js/place_order.js
document.addEventListener('DOMContentLoaded', () => {
    // build cart in memory (persisted in sessionStorage for UX)
    const CART_KEY = 'sds_cart_v1';
    const cart = loadCart();
  
    const productCards = Array.from(document.querySelectorAll('.card'));
    const cartDrawer = document.getElementById('cartDrawer');
    const openCartBtn = document.getElementById('openCartBtn');
    const closeCartBtn = document.getElementById('closeCartBtn');
    const cartItemsEl = document.getElementById('cartItems');
    const cartSubtotalEl = document.getElementById('cartSubtotal');
    const cartCountEl = document.getElementById('cartCount');
    const checkoutBtn = document.getElementById('checkoutBtn');
    const clearCartBtn = document.getElementById('clearCartBtn');
    const toast = document.getElementById('toast');
  
    // initialise quantity handlers on cards
    productCards.forEach(card => {
      const qtyEl = card.querySelector('.qty');
      const addBtn = card.querySelector('.add-btn');
      addBtn.addEventListener('click', () => {
        const id = card.dataset.id;
        const name = card.dataset.name;
        const price = Number(card.dataset.price);
        const img = card.dataset.img || '';
        const unit = card.querySelector('.desc')?.textContent?.toLowerCase() || '';
        const qty = Number(qtyEl.value);
        if (!qty || qty < 1) {
          showToast('Please enter a valid quantity (at least 1 pack)');
          return;
        }
        addToCart({ id, name, price, unit, img, qty });
        showToast(`${name} added to cart (${qty} pack${qty>1?'s':''})`);
      });
    });
  
    // cart drawer open/close
    openCartBtn.addEventListener('click', () => { renderCart(); cartDrawer.classList.add('open'); });
    closeCartBtn.addEventListener('click', () => cartDrawer.classList.remove('open'));
    clearCartBtn.addEventListener('click', () => { clearCart(); renderCart(); });
  
    // checkout
    checkoutBtn.addEventListener('click', () => {
      if (cart.items.length === 0) { showToast('Cart empty'); return; }
      // Use user_id from global JS variable (session)
      const customer_id = window.USER_ID;
      const payload = {
        customer_id,
  items: cart.items.map(i => ({ product_id: i.id, quantity: i.qty })),
  total_amount: cartTotal()
      };

      fetch('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      .then(r => r.json())
      .then(res => {
        if (res.success) {
          showToast('Order placed! Order Code: ' + (res.order_code || res.order_id));
          clearCart(); renderCart();
          cartDrawer.classList.remove('open');
        } else {
          showToast('Checkout failed: ' + (res.error || 'Unknown'));
        }
      })
      .catch(err => {
        showToast('Network error');
        console.error(err);
      });
    });
  
    // --- cart helpers ---
    function loadCart() {
      try {
        const raw = sessionStorage.getItem(CART_KEY);
        if (!raw) return { items: [] };
        return JSON.parse(raw);
      } catch (e) { return { items: [] }; }
    }
    function saveCart() { sessionStorage.setItem(CART_KEY, JSON.stringify(cart)); }
    function addToCart(item) {
      const existing = cart.items.find(i => i.id == item.id);
      if (existing) {
        // Set to entered value, not add
        existing.qty = item.qty;
        existing.price = item.price; // update price in case pack price changes
      } else {
        cart.items.push({ id: item.id, name: item.name, price: item.price, img: item.img, qty: item.qty });
      }
      saveCart();
      renderCart();
    }
    function updateQty(id, qty) {
      const it = cart.items.find(i => i.id == id);
      if (!it) return;
      it.qty = qty;
      if (it.qty <= 0) cart.items = cart.items.filter(x => x.id != id);
      saveCart();
      renderCart();
    }
    function clearCart() { cart.items = []; saveCart(); }
    function cartTotal() { return cart.items.reduce((s,i)=> s + (i.price * i.qty),0); }
  
    function renderCart() {
      cartItemsEl.innerHTML = '';
      cart.items.forEach(it => {
        const pieces = it.qty * 30;
        const div = document.createElement('div'); div.className = 'cart-item';
        div.innerHTML = `
          <img src="${it.img ? '/static/uploads/' + it.img : '/static/img/noimage.png'}" alt="${it.name}">
          <div class="meta">
            <div class="name">${it.name}</div>
            <div class="price">₹${(it.price * it.qty).toFixed(2)} <small style="color:#666">(${it.qty} pack${it.qty>1?'s':''}, ${pieces} pieces × ₹${it.price.toFixed(2)})</small></div>
          </div>
          <div class="qty-controls">
            <button class="dec">−</button>
            <span>${it.qty}</span>
            <button class="inc">+</button>
          </div>
        `;
        cartItemsEl.appendChild(div);

        div.querySelector('.dec').addEventListener('click', ()=> updateQty(it.id, it.qty - 1));
        div.querySelector('.inc').addEventListener('click', ()=> updateQty(it.id, it.qty + 1));
      });
  
      cartSubtotalEl.textContent = '₹' + cartTotal().toFixed(2);
      cartCountEl.textContent = cart.items.reduce((s,i)=> s + i.qty, 0);
    }
  
    function showToast(msg, ms = 2000) {
      toast.textContent = msg;
      toast.style.display = 'block';
      setTimeout(()=> toast.style.display = 'none', ms);
    }
  
    // initial render
    renderCart();
  });
  admin.js 
// Drop-down profile menu
document.addEventListener('DOMContentLoaded', function () {
    const btn = document.getElementById("profileBtn");
    const dropdown = document.getElementById("dropdownContent");
    if (btn && dropdown) {
        btn.onclick = function () {
            dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
        };
        window.onclick = function(event) {
            if (!event.target.matches('#profileBtn')) {
                dropdown.style.display = "none";
            }
        };
    }
});

// static/js/admin.js
document.addEventListener('DOMContentLoaded', function () {
    // Profile dropdown toggle
    document.getElementById('profileBtn')?.addEventListener('click', function () {
        document.getElementById('dropdownContent').classList.toggle('show');
    });

    /* ============ EDIT / DELETE HANDLERS ============ */
    function openEditModal(type, id, data) {
        const modal = document.getElementById('editModal');
        modal.querySelector('#editType').value = type;
        modal.querySelector('#editId').value = id;

        // Populate fields based on type
        let fieldsHtml = '';
        for (let key in data) {
            if (key === 'id' || key.endsWith('_id')) continue;
            fieldsHtml += `<label>${key}</label><input name="${key}" value="${data[key] || ''}"><br>`;
        }
        modal.querySelector('#editFields').innerHTML = fieldsHtml;
        modal.style.display = 'block';
    }

    function openConfirmDelete(type, id) {
        if (confirm(`Are you sure you want to delete this ${type}?`)) {
            fetch(`/admin/delete_${type}/${id}`, { method: 'DELETE' })
                .then(res => res.json())
                .then(d => {
                    alert(d.message || `${type} deleted`);
                    location.reload();
                });
        }
    }

    /* ============ ORDER DETAILS & STAFF ASSIGNMENT ============ */
    function openOrderDetails(orderId) {
        fetch(`/admin/order/${orderId}`)
            .then(res => res.json())
            .then(order => {
                const modal = document.getElementById('orderModal');
                const details = modal.querySelector('#orderDetails');
                details.innerHTML = `
                    <p><strong>Customer:</strong> ${order.customer.name}, ${order.customer.address}, ${order.customer.city}</p>
                    <p><strong>Status:</strong> ${order.status}</p>
                    <p><strong>Items:</strong></p>
                    <ul>${order.items.map(i => `<li>${i.name} x${i.quantity}</li>`).join('')}</ul>
                `;
                modal.querySelector('#assignStaffBtn').onclick = () => openStaffAssign(order.customer.city, orderId);
                modal.style.display = 'block';
            });
    }

    function openStaffAssign(customerCity, orderId) {
        fetch(`/admin/staff_near/${encodeURIComponent(customerCity)}`)
            .then(res => res.json())
            .then(staffList => {
                const assignModal = document.getElementById('staffAssignModal');
                const select = assignModal.querySelector('#staffSelect');
                select.innerHTML = staffList.map(s => `<option value="${s.staff_id}">${s.name} - ${s.city}</option>`).join('');
                assignModal.querySelector('#confirmAssignBtn').onclick = () => {
                    const staffId = select.value;
                    fetch(`/admin/assign_staff/${orderId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ staff_id: staffId })
                    })
                        .then(res => res.json())
                        .then(d => {
                            alert(d.message || 'Staff assigned');
                            assignModal.style.display = 'none';
                        });
                };
                assignModal.style.display = 'block';
            });
    }

    /* ============ MODAL CLOSES ============ */
    document.querySelectorAll('.modal .close').forEach(btn => {
        btn.addEventListener('click', function () {
            this.closest('.modal').style.display = 'none';
        });
    });

    // Attach event listeners dynamically (delegation)
    document.body.addEventListener('click', function (e) {
        if (e.target.matches('.edit-btn')) {
            const type = e.target.dataset.type;
            const id = e.target.dataset.id;
            const rowData = JSON.parse(e.target.dataset.data);
            openEditModal(type, id, rowData);
        }
        if (e.target.matches('.delete-btn')) {
            openConfirmDelete(e.target.dataset.type, e.target.dataset.id);
        }
        if (e.target.matches('.order-btn')) {
            openOrderDetails(e.target.dataset.id);
        }
    });
});