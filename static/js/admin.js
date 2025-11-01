// Drop-down profile menu
document.addEventListener('DOMContentLoaded', function () {
    const btn = document.getElementById("profileBtn");
    const dropdown = document.getElementById("dropdownContent");
    if (btn && dropdown) {
        btn.addEventListener('click', function (e) {
            e.stopPropagation();
            const isOpen = dropdown.style.display === 'block' || dropdown.classList.contains('show');
            if (isOpen) {
                dropdown.style.display = 'none';
                dropdown.classList.remove('show');
            } else {
                dropdown.style.display = 'block';
                dropdown.classList.add('show');
            }
        });
        // hide when clicking outside both button and dropdown
        document.addEventListener('click', function (event) {
            if (!btn.contains(event.target) && !dropdown.contains(event.target)) {
                dropdown.style.display = 'none';
                dropdown.classList.remove('show');
            }
        });
    }
});

    // static/js/admin.js
    document.addEventListener('DOMContentLoaded', function () {
    // NOTE: dropdown toggle handled above; keep rest of initialization here

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
                            location.reload(); // reload page to update orders table
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
        if (e.target.matches('.assign-staff-btn')) {
            const orderId = e.target.dataset.id;
            const city = e.target.dataset.city;
            openStaffAssign(city, orderId);
        }
    });
});
