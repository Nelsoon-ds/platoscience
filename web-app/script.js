const tableBody = document.getElementById("clinicTableBody");
const searchInput = document.getElementById("searchInput");
const countryFilter = document.getElementById("countryFilter");
const continentFilter = document.getElementById("continentFilter");
const contactFilter = document.getElementById("contactFilter");
const clinicCount = document.getElementById("clinicCount");
const jsonUpload = document.getElementById("jsonUpload");
const uploadStatus = document.getElementById("file-upload-status");
const paginationControls = document.getElementById("paginationControls");

const totalLeadsStat = document.getElementById("totalLeadsStat");
const emailLeadsStat = document.getElementById("emailLeadsStat");
const phoneLeadsStat = document.getElementById("phoneLeadsStat");
const countryCountStat = document.getElementById("countryCountStat");
const continentLeadsStat = document.getElementById("continentLeadsStat");
const continentLeadsTitle = document.getElementById("continentLeadsTitle");

let allClinics = [];
let filteredClinics = [];
let leadStatuses = {};
let currentSort = { key: "score", direction: "desc" };
let currentPage = 1;
const rowsPerPage = 20;

const countryToContinent = {
    USA: "North America",
    "United States": "North America",
    Canada: "North America",
    Mexico: "North America",
    Germany: "Europe",
    "United Kingdom": "Europe",
    France: "Europe",
    Italy: "Europe",
    Spain: "Europe",
    Switzerland: "Europe",
    Austria: "Europe",
    Belgium: "Europe",
    Netherlands: "Europe",
    Sweden: "Europe",
    Norway: "Europe",
    Denmark: "Europe",
    Finland: "Europe",
    Ireland: "Europe",
    Portugal: "Europe",
    Greece: "Europe",
    Poland: "Europe",
    Hungary: "Europe",
    Croatia: "Europe",
    Ukraine: "Europe",
    Australia: "Oceania",
    Japan: "Asia",
    Israel: "Asia",
    Turkey: "Asia",
    Thailand: "Asia",
    Taiwan: "Asia",
    "Hong Kong": "Asia",
    Singapore: "Asia",
    India: "Asia",
    Philippines: "Asia",
    Nepal: "Asia",
    "South Africa": "Africa",
    Brazil: "South America",
    Ecuador: "South America",
    Chile: "South America",
    Peru: "South America",
    Paraguay: "South America",
};

function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function (e) {
        try {
            const rawData = JSON.parse(e.target.result);
            allClinics = rawData.map((c) => ({
                ...c,
                continent: countryToContinent[c.country] || "Other",
                score: calculateLeadScore(c),
            }));

            uploadStatus.textContent = `Successfully loaded ${allClinics.length} clinics from ${file.name}.`;
            uploadStatus.className = "text-sm text-green-600 mt-2";
            loadStatuses();
            populateContinentFilter();
            populateCountryFilter();
            updateStatistics();
            filterData();
        } catch (error) {
            uploadStatus.textContent = `Error parsing JSON file: ${error.message}`;
            uploadStatus.className = "text-sm text-red-600 mt-2";
        }
    };
    reader.readAsText(file);
}

function calculateLeadScore(clinic) {
    let score = 0;
    if (clinic.email) score += 3;
    if (clinic.phone) score += 2;
    if (clinic.website && clinic.website !== "#") score += 1;
    return score;
}

function updateStatistics() {
    totalLeadsStat.textContent = allClinics.length;
    emailLeadsStat.textContent = allClinics.filter((c) => c.email).length;
    phoneLeadsStat.textContent = allClinics.filter((c) => c.phone).length;
    countryCountStat.textContent = [
        ...new Set(
            allClinics.map((c) => c.country).filter((c) => c && c !== "N/A")
        ),
    ].length;
}

function populateContinentFilter() {
    continentFilter.innerHTML = '<option value="">All Continents</option>';
    const continents = [...new Set(allClinics.map((c) => c.continent))].sort();
    continents.forEach((continent) => {
        const option = document.createElement("option");
        option.value = continent;
        option.textContent = continent;
        continentFilter.appendChild(option);
    });
}

function populateCountryFilter(selectedContinent = "") {
    countryFilter.innerHTML = '<option value="">All Countries</option>';
    const countries = [
        ...new Set(
            allClinics
                .filter((c) =>
                    selectedContinent ? c.continent === selectedContinent : true
                )
                .map((c) => c.country)
                .filter(Boolean)
        ),
    ].sort();

    countries.forEach((country) => {
        const option = document.createElement("option");
        option.value = country;
        option.textContent = country;
        countryFilter.appendChild(option);
    });
}

function renderTable() {
    // Sort the already filtered data
    filteredClinics.sort((a, b) => {
        const valA = a[currentSort.key];
        const valB = b[currentSort.key];
        let comparison = 0;
        if (valA > valB) {
            comparison = 1;
        } else if (valA < valB) {
            comparison = -1;
        }
        return currentSort.direction === "asc" ? comparison : -comparison;
    });

    const startIndex = (currentPage - 1) * rowsPerPage;
    const endIndex = startIndex + rowsPerPage;
    const paginatedClinics = filteredClinics.slice(startIndex, endIndex);

    if (paginatedClinics.length === 0) {
        tableBody.innerHTML =
            '<tr><td colspan="6" class="p-4 text-center text-gray-500">No clinics match your search.</td></tr>';
    } else {
        let tableHTML = "";
        paginatedClinics.forEach((clinic) => {
            const status = leadStatuses[clinic.name] || "New";
            const sanitizedName = (clinic.name || "")
                .replace(/["“”]/g, "&quot;")
                .replace(/'/g, "&#39;");
            tableHTML += `
                <tr class="border-b border-gray-200 hover:bg-gray-50">
                    <td class="p-4 align-top">
                        <div class="font-bold text-gray-900">${
                            clinic.name
                        }</div>
                        <a href="${
                            clinic.website
                        }" target="_blank" class="text-blue-600 hover:underline text-sm">${
                clinic.website !== "#" ? clinic.website : ""
            }</a>
                    </td>
   <td class="p-4 align-top text-sm text-gray-600">

    <div title="${clinic.address || ""}">${
                truncate(clinic.address, 70) || ""
            }</div>
    <span class="font-medium">${clinic.city || ""}, ${
                clinic.country || ""
            }</span>
</td>
                    <td class="p-4 align-top text-sm">
                        ${
                            clinic.email
                                ? `<a href="mailto:${clinic.email}" class="text-blue-600 hover:underline">${clinic.email}</a><br>`
                                : ""
                        }
                        ${
                            clinic.phone
                                ? `<span class="text-gray-600">${clinic.phone}</span>`
                                : ""
                        }
                    </td>
                    <td class="p-4 align-top text-center font-bold text-lg ${
                        clinic.score > 4
                            ? "text-green-600"
                            : clinic.score > 2
                            ? "text-yellow-600"
                            : "text-red-600"
                    }">${clinic.score}</td>
                    <td class="p-4 align-top text-sm text-gray-500">${
                        clinic.source
                    }</td>
                    <td class="p-4 align-top">
                        <select class="status-dropdown p-2 border border-gray-300 rounded-md" data-clinic-name="${sanitizedName}">
                            <option value="New" ${
                                status === "New" ? "selected" : ""
                            }>New</option>
                            <option value="Contacted" ${
                                status === "Contacted" ? "selected" : ""
                            }>Contacted</option>
                            <option value="Engaged" ${
                                status === "Engaged" ? "selected" : ""
                            }>Engaged</option>
                            <option value="Qualified" ${
                                status === "Qualified" ? "selected" : ""
                            }>Qualified</option>
                            <option value="Not a Fit" ${
                                status === "Not a Fit" ? "selected" : ""
                            }>Not a Fit</option>
                        </select>
                    </td>
                </tr>
            `;
        });
        tableBody.innerHTML = tableHTML;
    }

    clinicCount.textContent = filteredClinics.length;
    renderPaginationControls(filteredClinics.length);
    addStatusListeners();
}

function renderPaginationControls(totalItems) {
    paginationControls.innerHTML = "";
    const totalPages = Math.ceil(totalItems / rowsPerPage);
    if (totalPages <= 1) return;

    const startItem = (currentPage - 1) * rowsPerPage + 1;
    const endItem = Math.min(currentPage * rowsPerPage, totalItems);

    const summary = document.createElement("p");
    summary.className = "text-sm text-gray-700";
    summary.textContent = `Showing ${startItem} to ${endItem} of ${totalItems} results`;

    const buttonsDiv = document.createElement("div");
    buttonsDiv.className = "flex gap-2";

    const prevButton = document.createElement("button");
    prevButton.textContent = "Previous";
    prevButton.className = "pagination-btn";
    prevButton.disabled = currentPage === 1;
    prevButton.addEventListener("click", () => {
        currentPage--;
        renderTable();
    });

    const nextButton = document.createElement("button");
    nextButton.textContent = "Next";
    nextButton.className = "pagination-btn";
    nextButton.disabled = currentPage === totalPages;
    nextButton.addEventListener("click", () => {
        currentPage++;
        renderTable();
    });

    buttonsDiv.appendChild(prevButton);
    buttonsDiv.appendChild(nextButton);
    paginationControls.appendChild(summary);
    paginationControls.appendChild(buttonsDiv);
}

function filterData() {
    const searchTerm = searchInput.value.toLowerCase();
    const selectedCountry = countryFilter.value;
    const selectedContinent = continentFilter.value;
    const selectedContact = contactFilter.value;

    filteredClinics = allClinics.filter((clinic) => {
        const c = clinic; // alias for brevity
        const matchesSearch =
            c.name.toLowerCase().includes(searchTerm) ||
            (c.country && c.country.toLowerCase().includes(searchTerm)) ||
            (c.city && c.city.toLowerCase().includes(searchTerm));
        const matchesContinent =
            !selectedContinent || c.continent === selectedContinent;
        const matchesCountry =
            !selectedCountry || c.country === selectedCountry;
        const matchesContact =
            !selectedContact ||
            (selectedContact === "phoneAndEmail" && c.phone && c.email) ||
            (selectedContact === "phoneOnly" && c.phone) ||
            (selectedContact === "emailOnly" && c.email);
        return (
            matchesSearch &&
            matchesContinent &&
            matchesCountry &&
            matchesContact
        );
    });

    currentPage = 1;

    if (selectedContinent) {
        continentLeadsTitle.textContent = `Leads in ${selectedContinent}`;
        const continentCount = allClinics.filter(
            (c) => c.continent === selectedContinent
        ).length;
        continentLeadsStat.textContent = continentCount;
    } else {
        continentLeadsTitle.textContent = "Leads in Continent";
        continentLeadsStat.textContent = "N/A";
    }

    renderTable();
}

function saveStatus(clinicName, status) {
    leadStatuses[clinicName] = status;
    localStorage.setItem("leadStatuses", JSON.stringify(leadStatuses));
}

function loadStatuses() {
    const saved = localStorage.getItem("leadStatuses");
    if (saved) {
        leadStatuses = JSON.parse(saved);
    }
}

function addStatusListeners() {
    document.querySelectorAll(".status-dropdown").forEach((dropdown) => {
        dropdown.addEventListener("change", (e) => {
            const clinicName = e.target.dataset.clinicName;
            const newStatus = e.target.value;
            saveStatus(clinicName, newStatus);
        });
    });
}

function handleSort(e) {
    const key = e.target.dataset.sort;
    if (!key) return;

    document.querySelectorAll(".sortable").forEach((th) => {
        if (th !== e.target) {
            th.classList.remove("sort-asc", "sort-desc");
        }
    });

    if (currentSort.key === key) {
        currentSort.direction =
            currentSort.direction === "asc" ? "desc" : "asc";
    } else {
        currentSort.key = key;
        currentSort.direction = "asc";
    }

    e.target.classList.remove("sort-asc", "sort-desc");
    e.target.classList.add(
        currentSort.direction === "asc" ? "sort-asc" : "sort-desc"
    );

    renderTable();
}

/**
 * Truncates a string to a specified length and adds an ellipsis.
 * @param {string} str The string to truncate.
 * @param {number} maxLength The maximum length of the string.
 * @returns {string} The truncated string.
 */
function truncate(str, maxLength) {
    if (!str || str.length <= maxLength) {
        return str;
    }
    return str.substring(0, maxLength) + "...";
}

// Initial Event Listeners
searchInput.addEventListener("input", filterData);
countryFilter.addEventListener("change", filterData);
continentFilter.addEventListener("change", (e) => {
    populateCountryFilter(e.target.value);
    filterData();
});
contactFilter.addEventListener("change", filterData);
jsonUpload.addEventListener("change", handleFileUpload);
document.querySelectorAll(".sortable").forEach((header) => {
    header.addEventListener("click", handleSort);
});
