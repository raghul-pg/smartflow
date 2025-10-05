// Toggle dropdown
document.getElementById('profileBtn').addEventListener('click', function () {
    const dropdown = document.getElementById('dropdownContent');
    dropdown.classList.toggle('show');
});

// Close dropdown if clicked outside
window.addEventListener('click', function(e) {
    if (!e.target.matches('#profileBtn')) {
        const dropdown = document.getElementById('dropdownContent');
        if (dropdown.classList.contains('show')) {
            dropdown.classList.remove('show');
        }
    }
});

window.USER_ID = window.USER_ID || document.querySelector('[id^="profileBtn"]').getAttribute('data-user-id') || '';
document.addEventListener('DOMContentLoaded', function() {
    const viewBtn = document.getElementById('viewOrdersBtn');
    const ordersSection = document.getElementById('ordersSection');
    const ordersList = document.getElementById('ordersList');
    const closeBtn = document.getElementById('closeOrdersBtn');
    const paymentModal = document.getElementById('paymentModal');
    const paymentOrderId = document.getElementById('paymentOrderId');
    const paymentAmount = document.getElementById('paymentAmount');
    const manualPaymentBtn = document.getElementById('manualPaymentBtn');
    const cardPaymentBtn = document.getElementById('cardPaymentBtn');

    function fetchOrders() {
        ordersList.textContent = 'Loading...';
        fetch(`/api/customer_orders/${window.USER_ID}`)
            .then(r => r.json())
            .then(orders => {
                if (!orders.length) { 
                    ordersList.textContent = 'No orders found.'; 
                    return; 
                }
                ordersList.innerHTML = orders.map(o => {
                    const isPaid = o.payment_status && o.payment_status.toLowerCase() === 'paid';
                    return `
                    <div class="order-card" data-order-id="${o.id}" style="border:1px solid #ccc; padding:1em; margin-bottom:1em;">
                        <div><strong>Order Code:</strong> ${o.order_code}</div>
                        <div><strong>Status:</strong> ${o.status}</div>
                        <div><strong>Date:</strong> ${o.order_date}</div>
                        <div><strong>Warehouse:</strong> ${o.warehouse_name}</div>
                        <div><strong>Total:</strong> ₹${o.total_amount}</div>
                        <div><strong>Distance:</strong> ${o.distance_km} km</div>
                        <div><strong>Transport Cost:</strong> ₹${o.transport_cost}</div>
                        <div><strong>Estimated Time:</strong> ${o.transport_time_hours} hours</div>
                        <div><strong>Payment Status:</strong> ${o.payment_status || 'Pending'}</div>
                        <div><strong>Payment Mode:</strong> ${o.payment_mode || 'Not selected'}</div>
                        <div><strong>Items:</strong>
                            <ul style="margin:0;">
                                ${o.items.map(i => `<li>${i.name} × ${i.quantity}</li>`).join('')}
                            </ul>
                        </div>
                        <button class="track-delivery-btn" data-order-id="${o.id}" style="margin-top:10px;">Track Delivery</button>
                        ${isPaid ? 
                            '<p style="color:green;margin-top:10px;">Payment Completed</p>' : 
                            `<button class="pay-now-btn" data-order-id="${o.id}" data-amount="${o.total_amount}" style="background:#0077cc;color:white;padding:10px 20px;border:none;border-radius:5px;margin-top:10px;">Pay Now</button>`
                        }
                    </div>
                `;
                }).join('');
            })
            .catch(()=>{ ordersList.textContent = 'Failed to load orders.'; });
    }

    viewBtn.addEventListener('click', function() {
        ordersSection.style.display = 'block';
        fetchOrders();
    });

    closeBtn.addEventListener('click', function() {
        ordersSection.style.display = 'none';
    });

    ordersList.addEventListener('click', function(e) {
        if (e.target.classList.contains('track-delivery-btn')) {
            const orderId = e.target.getAttribute('data-order-id');
            fetch(`/api/order_status/${orderId}`)
                .then(res => res.json())
                .then(data => {
                    if (!data.success) { 
                        alert('Tracking info not available.'); 
                        return; 
                    }
                    renderTrackingSteps(data.status, data.dates || {});
                    document.getElementById('trackDeliveryModal').style.display = 'flex';
                })
                .catch(() => {
                    alert('Error fetching tracking information');
                });
        }

        if (e.target.classList.contains('pay-now-btn')) {
            const orderId = e.target.getAttribute('data-order-id');
            const amount = e.target.getAttribute('data-amount');
            paymentOrderId.textContent = orderId;
            paymentAmount.textContent = amount;
            paymentModal.style.display = 'flex';
            document.getElementById('submitManualPaymentBtn').setAttribute('data-order-id', orderId);
        }
    });

    if (manualPaymentBtn) {
        manualPaymentBtn.addEventListener('click', async function() {
            // Removed
        });
    }
    if (cardPaymentBtn) {
        cardPaymentBtn.addEventListener('click', async function() {
            // Removed
        });
    }

    async function updatePaymentMode(orderId, mode) {
        try {
            const transactionId = document.getElementById('transactionIdInput').value.trim();
            if (!transactionId) {
                alert('Please enter your transaction/reference ID.');
                return;
            }
            const res = await fetch('/api/update_payment_mode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ order_id: orderId, payment_mode: 'manual_upi', transaction_id: transactionId })
            });
            const data = await res.json();
            if (data.success) {
                alert('Payment info submitted. We will verify and update your order status soon.');
                fetchOrders();
                paymentModal.style.display = 'none';
            } else {
                alert('Failed to submit payment info: ' + data.message);
            }
        } catch (err) {
            alert('Error submitting payment info');
        }
    }
    document.getElementById('submitManualPaymentBtn').addEventListener('click', async function() {
        const orderId = this.getAttribute('data-order-id');
        await updatePaymentMode(orderId, 'manual_upi');
    });
});