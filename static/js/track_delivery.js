// Track Delivery Modal Logic
// Assumes order status is fetched from backend via API
// Example statuses: ['Order Confirmed', 'Shipped', 'Out For Delivery', 'Delivered']

const statusSteps = [
  { key: 'confirmed', label: 'Order Confirmed' },
  { key: 'shipped', label: 'Shipped' },
  { key: 'out_for_delivery', label: 'Out For Delivery' },
  { key: 'delivered', label: 'Delivery' }
];

// Dummy: Replace with actual order id selection logic
let currentOrderId = null;

function fetchOrderStatus(orderId) {
  // Replace with real API call
  return fetch(`/api/order_status/${orderId}`)
    .then(res => res.json());
}

function renderTrackingSteps(status, dateMap) {
  let html = '<div style="border-left:4px solid #4caf50;padding-left:20px;">';
  for (let i = 0; i < statusSteps.length; i++) {
    const step = statusSteps[i];
    const done = status[step.key];
    html += `<div style="margin-bottom:18px;display:flex;align-items:center;">
      <span style="display:inline-block;width:22px;height:22px;border-radius:50%;background:${done?'#4caf50':'#fff'};border:2px solid #4caf50;margin-right:10px;vertical-align:middle;text-align:center;line-height:18px;font-size:18px;color:${done?'#fff':'#4caf50'};">${done?'✓':''}</span>
      <span style="font-weight:${done?'bold':'normal'};background:${done?'#e8f5e9':'none'};padding:2px 8px;border-radius:4px;">${step.label}${dateMap[step.key]?`, ${dateMap[step.key]}`:''}</span>
    </div>`;
  }
  html += '</div>';
  document.getElementById('trackingSteps').innerHTML = html;
}

document.getElementById('trackDeliveryBtn').onclick = function() {
  // For demo, use first order or prompt user to select
  let orderId = currentOrderId;
  if (!orderId) {
    // Try to get from first order row (customize as needed)
    const row = document.querySelector('tr[data-order-id]');
    if (row) orderId = row.getAttribute('data-order-id');
  }
  if (!orderId) {
    alert('No order selected.');
    return;
  }
  fetchOrderStatus(orderId).then(data => {
    renderTrackingSteps(data.status, data.dates||{});
    document.getElementById('trackDeliveryModal').style.display = 'flex';
  });
};
