function navigateToRegister() {
    let role = document.getElementById("roleSelect").value;
    document.getElementById("customerRegister").classList.add("hidden");
    document.getElementById("staffRegister").classList.add("hidden");
    document.getElementById("customerResult").classList.add("hidden");
    document.getElementById("staffResult").classList.add("hidden");

    if (role === "customer") {
        document.getElementById("customerRegister").classList.remove("hidden");
    } else if (role === "staff") {
        document.getElementById("staffRegister").classList.remove("hidden");
    }
}
function showForm(role) {
    document.getElementById("roleSelection").classList.add("hidden");

    if (role === "customer") {
        document.getElementById("customerRegister").classList.remove("hidden");
    } else if (role === "staff") {
        document.getElementById("staffRegister").classList.remove("hidden");
    }
}

function goBack() {
    document.getElementById("customerRegister").classList.add("hidden");
    document.getElementById("staffRegister").classList.add("hidden");
    document.getElementById("roleSelection").classList.remove("hidden");
}

document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("customerForm").addEventListener("submit", registerCustomer);
    document.getElementById("staffForm").addEventListener("submit", registerStaff);
});

// The registerCustomer and registerStaff functions remain the same from your original code

document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("customerForm").addEventListener("submit", registerCustomer);
    document.getElementById("staffForm").addEventListener("submit", registerStaff);
});

async function registerCustomer(event) {
    event.preventDefault();

    const customerData = {
        name: document.getElementById("customer_name").value,
        email: document.getElementById("customer_email").value,
        phone: document.getElementById("customer_phone").value,
        city: document.getElementById("customer_city").value,
        state: document.getElementById("customer_state").value,
        zip_code: document.getElementById("customer_zipcode").value,
        country: document.getElementById("customer_country").value,
        address: document.getElementById("customer_address").value
    };

    const response = await fetch('/register/customer', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(customerData)
    });

    if (response.ok) {
        const result = await response.json();
        document.getElementById("generatedCustomerId").innerText = result.customer_id;
        document.getElementById("generatedCustomerPassword").innerText = result.password;
        document.getElementById("customerResult").classList.remove("hidden");
    } else {
        alert("Customer registration failed.");
    }
}

async function registerStaff(event) {
    event.preventDefault();

    const staffData = {
        name: document.getElementById("staff_name").value,
        email: document.getElementById("staff_email").value,
        phone: document.getElementById("staff_phone").value,
        age: document.getElementById("staff_age").value,
        city: document.getElementById("staff_city").value,
        address: document.getElementById("staff_address").value
    };

    const response = await fetch('/register/staff', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(staffData)
    });

    if (response.ok) {
        const result = await response.json();
        document.getElementById("generatedStaffId").innerText = result.staff_id;
        document.getElementById("generatedStaffPassword").innerText = result.password;
        document.getElementById("staffResult").classList.remove("hidden");
    } else {
        alert("Staff registration failed.");
    }
}
