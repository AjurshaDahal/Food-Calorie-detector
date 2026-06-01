/**
 * BhojanLens — Frontend Application
 */

// Category groupings for filter tabs
const CATEGORY_GROUPS = {
    asian: ['japanese', 'korean', 'thai', 'vietnamese', 'asian', 'indian'],
    western: ['american', 'italian', 'mexican', 'breakfast'],
    dessert: ['dessert'],
    healthy: ['salad', 'seafood'],
};

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements 
    const dropZone = document.getElementById('drop-zone');
    const dropContent = document.getElementById('drop-zone-content');
    const previewContainer = document.getElementById('preview-container');
    const imagePreview = document.getElementById('image-preview');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');
    const removeImage = document.getElementById('remove-image');
    const analyzeBtn = document.getElementById('analyze-btn');
    const countSection = document.getElementById('count-section');
    const itemCount = document.getElementById('item-count');
    const countDecrease = document.getElementById('count-decrease');
    const countIncrease = document.getElementById('count-increase');
    const resultsCard = document.getElementById('results-card');
    const foodGrid = document.getElementById('food-grid');
    const foodSearch = document.getElementById('food-search');
    const filterTabs = document.querySelectorAll('.filter-tab');
    const manualResult = document.getElementById('manual-result');
    const closeManualResult = document.getElementById('close-manual-result');
    const navLinks = document.querySelectorAll('.nav-link');

    let selectedFile = null;
    let allFoods = [];
    let activeFilter = 'all';
    let modalOverlay = null;

    // Initialize 
    loadFoodDatabase();
    setupEventListeners();

    function setupEventListeners() {
        // File handling
        browseBtn.addEventListener('click', e => { e.stopPropagation(); fileInput.click(); });
        dropZone.addEventListener('click', () => { if (!selectedFile) fileInput.click(); });
        fileInput.addEventListener('change', handleFileSelect);
        removeImage.addEventListener('click', e => { e.stopPropagation(); clearImage(); });

        // Drag and drop
        ['dragenter', 'dragover'].forEach(e => {
            dropZone.addEventListener(e, ev => { ev.preventDefault(); dropZone.classList.add('drag-over'); });
        });
        ['dragleave', 'drop'].forEach(e => {
            dropZone.addEventListener(e, ev => { ev.preventDefault(); dropZone.classList.remove('drag-over'); });
        });
        dropZone.addEventListener('drop', handleDrop);

        // Analysis
        analyzeBtn.addEventListener('click', analyzeFood);

        // Count controls
        countDecrease.addEventListener('click', () => {
            const v = parseInt(itemCount.value) || 1;
            if (v > 1) itemCount.value = v - 1;
        });
        countIncrease.addEventListener('click', () => {
            const v = parseInt(itemCount.value) || 1;
            if (v < 100) itemCount.value = v + 1;
        });

        // Search and filter
        foodSearch.addEventListener('input', filterFoods);
        filterTabs.forEach(tab => tab.addEventListener('click', () => {
            filterTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            activeFilter = tab.dataset.filter;
            filterFoods();
        }));

        // Modal
        closeManualResult.addEventListener('click', closeModal);

        // Smooth nav
        navLinks.forEach(link => link.addEventListener('click', e => {
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        }));
    }

    // File Handling 
    function handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) loadFile(file);
    }

    function handleDrop(e) {
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) loadFile(file);
    }

    function loadFile(file) {
        if (file.size > 16 * 1024 * 1024) {
            alert('File too large. Maximum size is 16MB.');
            return;
        }
        selectedFile = file;
        const reader = new FileReader();
        reader.onload = e => {
            imagePreview.src = e.target.result;
            dropContent.style.display = 'none';
            previewContainer.style.display = 'block';
            countSection.style.display = 'block';
            analyzeBtn.disabled = false;
            imagePreview.style.animation = 'fadeInUp 0.4s ease-out';
        };
        reader.readAsDataURL(file);
    }

    function clearImage() {
        selectedFile = null;
        fileInput.value = '';
        imagePreview.src = '';
        dropContent.style.display = 'flex';
        previewContainer.style.display = 'none';
        countSection.style.display = 'none';
        analyzeBtn.disabled = true;
        resultsCard.style.display = 'none';
        const infoCard = document.getElementById('info-card');
        if (infoCard) infoCard.style.display = 'flex';
    }

    // Food Analysis 
    async function analyzeFood() {
        if (!selectedFile) return;
        const btnContent = analyzeBtn.querySelector('.btn-content');
        const btnLoader = analyzeBtn.querySelector('.btn-loader');
        btnContent.style.display = 'none';
        btnLoader.style.display = 'flex';
        analyzeBtn.disabled = true;

        const formData = new FormData();
        formData.append('image', selectedFile);
        const count = parseInt(itemCount.value);
        if (count > 1) formData.append('item_count', count);

        try {
            const res = await fetch('/api/analyze', { method: 'POST', body: formData });
            const data = await res.json();
            displayResults(data);
        } catch (err) {
            displayError('Network error. Please ensure the server is running.');
        } finally {
            btnContent.style.display = 'flex';
            btnLoader.style.display = 'none';
            analyzeBtn.disabled = false;
        }
    }

    function displayResults(data) {
        resultsCard.style.display = 'block';
        const infoCard = document.getElementById('info-card');
        if (infoCard) infoCard.style.display = 'none';
        resultsCard.style.animation = 'fadeInUp 0.5s ease-out';
        const detected = document.getElementById('detected-info');
        const notDetected = document.getElementById('not-detected-info');
        const predictions = document.getElementById('predictions-section');

        if (data.success && data.detected) {
            detected.style.display = 'block';
            notDetected.style.display = 'none';
            document.getElementById('results-icon').textContent = '✅';
            document.getElementById('results-title').textContent = 'Food Detected!';
            document.getElementById('results-subtitle').textContent = `Model: ${data.model_used} • Confidence: ${data.confidence}%`;

            const n = data.nutrition;
            document.getElementById('food-name').textContent = n.food_name;
            document.getElementById('food-description').textContent = n.description;
            document.getElementById('confidence-fill').style.width = data.confidence + '%';
            document.getElementById('confidence-value').textContent = data.confidence + '%';

            // Color the confidence bar based on value
            const confFill = document.getElementById('confidence-fill');
            if (data.confidence >= 80) confFill.style.background = 'var(--success)';
            else if (data.confidence >= 50) confFill.style.background = 'var(--accent-secondary)';
            else confFill.style.background = 'var(--accent-primary)';

            animateNumber('calorie-number', n.total_calories);
            document.getElementById('serving-value').textContent = n.serving_size;

            const countInfo = document.getElementById('count-info');
            if (n.count > 1) {
                countInfo.style.display = 'flex';
                document.getElementById('count-value').textContent = `${n.count} items × ${n.calories_per_unit} kcal`;
            } else { countInfo.style.display = 'none'; }

            // Macros
            document.getElementById('protein-value').textContent = n.protein_g + 'g';
            document.getElementById('carbs-value').textContent = n.carbs_g + 'g';
            document.getElementById('fat-value').textContent = n.fat_g + 'g';
            document.getElementById('fiber-value').textContent = n.fiber_g + 'g';
            const total = n.protein_g + n.carbs_g + n.fat_g + n.fiber_g || 1;
            document.getElementById('protein-bar').style.width = (n.protein_g / total * 100) + '%';
            document.getElementById('carbs-bar').style.width = (n.carbs_g / total * 100) + '%';
            document.getElementById('fat-bar').style.width = (n.fat_g / total * 100) + '%';
            document.getElementById('fiber-bar').style.width = (n.fiber_g / total * 100) + '%';

            // Calorie ring
            const maxCal = 800;
            const pct = Math.min(n.total_calories / maxCal, 1);
            const ring = document.getElementById('calorie-ring-fill');
            setTimeout(() => { ring.style.strokeDashoffset = 440 - (440 * pct); }, 100);

            if (data.note) {
                document.getElementById('result-note').style.display = 'flex';
                document.getElementById('note-text').textContent = data.note;
            }
        } else if (data.success && !data.detected) {
            detected.style.display = 'none';
            notDetected.style.display = 'block';
            document.getElementById('results-icon').textContent = '🤔';
            document.getElementById('results-title').textContent = 'Food Not Recognized';
            document.getElementById('results-subtitle').textContent = '';
            document.getElementById('not-detected-message').textContent = data.message;
            document.getElementById('not-detected-suggestion').textContent = data.suggestion || '';
        } else {
            displayError(data.error || 'Unknown error occurred.');
            return;
        }

        // Top predictions
        if (data.top_predictions && data.top_predictions.length) {
            predictions.style.display = 'block';
            const list = document.getElementById('predictions-list');
            list.innerHTML = data.top_predictions.map(p =>
                `<div class="prediction-item">
                    <span class="pred-name">${p.class}</span>
                    <span class="pred-conf">${p.confidence}%</span>
                </div>`
            ).join('');
        } else { predictions.style.display = 'none'; }

        resultsCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    function displayError(msg) {
        resultsCard.style.display = 'block';
        const infoCard = document.getElementById('info-card');
        if (infoCard) infoCard.style.display = 'none';
        document.getElementById('detected-info').style.display = 'none';
        document.getElementById('not-detected-info').style.display = 'block';
        document.getElementById('predictions-section').style.display = 'none';
        document.getElementById('results-icon').textContent = '❌';
        document.getElementById('results-title').textContent = 'Error';
        document.getElementById('results-subtitle').textContent = '';
        document.getElementById('not-detected-message').textContent = msg;
        document.getElementById('not-detected-suggestion').textContent = '';
    }

    function animateNumber(id, target) {
        const el = document.getElementById(id);
        const dur = 1200;
        const start = performance.now();
        function update(now) {
            const p = Math.min((now - start) / dur, 1);
            const ease = 1 - Math.pow(1 - p, 3);
            el.textContent = Math.round(target * ease);
            if (p < 1) requestAnimationFrame(update);
        }
        requestAnimationFrame(update);
    }

    // Food Database 
    async function loadFoodDatabase() {
        try {
            const res = await fetch('/api/foods');
            const data = await res.json();
            if (data.success) { allFoods = data.foods; renderFoods(allFoods); }
        } catch { renderFoodsOffline(); }
    }

    function renderFoodsOffline() {
        foodGrid.innerHTML = '<p style="text-align:center;color:var(--text-muted);grid-column:1/-1;padding:40px;">Connect to the server to browse the food database.</p>';
    }

    function filterFoods() {
        const q = foodSearch.value.toLowerCase();
        const filtered = allFoods.filter(f => {
            // Category-based filtering
            let matchFilter = true;
            if (activeFilter !== 'all') {
                const groupCategories = CATEGORY_GROUPS[activeFilter] || [];
                matchFilter = groupCategories.includes(f.category);
            }
            const matchSearch = !q || f.name.toLowerCase().includes(q) ||
                f.category.toLowerCase().includes(q);
            return matchFilter && matchSearch;
        });
        renderFoods(filtered);
    }

    function renderFoods(foods) {
        if (!foods.length) {
            foodGrid.innerHTML = '<p style="text-align:center;color:var(--text-muted);grid-column:1/-1;padding:40px;">No matching foods found.</p>';
            return;
        }
        foodGrid.innerHTML = foods.map(f => `
            <div class="food-card" data-key="${f.key}" onclick="window.__lookupFood('${f.key}')">
                <div class="food-card-header">
                    <div>
                        <span class="food-card-emoji">${f.emoji || '🍽️'}</span>
                        <span class="food-card-name">${f.name}</span>
                    </div>
                    <span class="food-card-badge">${f.category.replace('_', ' ')}</span>
                </div>
                <div class="food-card-cal">${f.calories} <span>kcal / ${f.serving_size}</span></div>
                <div class="food-card-macros">
                    <span class="mini-macro">P: ${f.protein_g}g</span>
                    <span class="mini-macro">C: ${f.carbs_g}g</span>
                    <span class="mini-macro">F: ${f.fat_g}g</span>
                </div>
            </div>
        `).join('');
    }

    // Manual Lookup
    window.__lookupFood = async function (key) {
        try {
            const res = await fetch('/api/manual-lookup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ food_key: key })
            });
            const data = await res.json();
            if (data.success) showModal(data.nutrition);
        } catch { alert('Could not fetch food details.'); }
    };

    function showModal(n) {
        modalOverlay = document.createElement('div');
        modalOverlay.className = 'modal-overlay';
        modalOverlay.addEventListener('click', closeModal);
        document.body.appendChild(modalOverlay);

        const total = n.protein_g + n.carbs_g + n.fat_g + n.fiber_g || 1;
        document.getElementById('manual-result-content').innerHTML = `
            <div style="text-align:center;margin-bottom:20px;">
                <h3 style="font-size:24px;font-weight:800;">${n.food_name}</h3>
                <p style="font-size:14px;color:var(--text-secondary);margin-top:8px;">${n.description}</p>
            </div>
            <div style="text-align:center;margin-bottom:20px;">
                <span style="font-size:48px;font-weight:900;color:var(--accent-primary);">${n.total_calories}</span>
                <span style="font-size:14px;color:var(--text-muted);display:block;">kcal total</span>
                <span style="font-size:13px;color:var(--text-secondary);">${n.serving_size}${n.count > 1 ? ' × ' + n.count : ''}</span>
            </div>
            <div class="macros-grid" style="grid-template-columns:repeat(2,1fr);">
                <div class="macro-card macro-protein"><div class="macro-icon">🥩</div><span class="macro-value">${n.protein_g}g</span><span class="macro-label">Protein</span><div class="macro-bar"><div class="macro-bar-fill" style="width:${n.protein_g / total * 100}%;background:var(--info);"></div></div></div>
                <div class="macro-card macro-carbs"><div class="macro-icon">🌾</div><span class="macro-value">${n.carbs_g}g</span><span class="macro-label">Carbs</span><div class="macro-bar"><div class="macro-bar-fill" style="width:${n.carbs_g / total * 100}%;background:var(--accent-secondary);"></div></div></div>
                <div class="macro-card macro-fat"><div class="macro-icon">🫒</div><span class="macro-value">${n.fat_g}g</span><span class="macro-label">Fat</span><div class="macro-bar"><div class="macro-bar-fill" style="width:${n.fat_g / total * 100}%;background:var(--accent-primary);"></div></div></div>
                <div class="macro-card macro-fiber"><div class="macro-icon">🥬</div><span class="macro-value">${n.fiber_g}g</span><span class="macro-label">Fiber</span><div class="macro-bar"><div class="macro-bar-fill" style="width:${n.fiber_g / total * 100}%;background:var(--success);"></div></div></div>
            </div>`;
        manualResult.style.display = 'block';
        manualResult.style.animation = 'fadeInUp 0.3s ease-out';
    }

    function closeModal() {
        manualResult.style.display = 'none';
        if (modalOverlay) { modalOverlay.remove(); modalOverlay = null; }
    }
});
