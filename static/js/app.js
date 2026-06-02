const categories = {
    asian: ['japanese', 'korean', 'thai', 'vietnamese', 'asian', 'indian', 'nepali'],
    western: ['american', 'italian', 'mexican', 'breakfast'],
    dessert: ['dessert'],
    healthy: ['salad', 'seafood'],
};

// Cute food emojis based on category or name
function getFoodEmoji(item) {
    const name = item.name.toLowerCase();
    if (name.includes('pizza')) return '🍕';
    if (name.includes('burger')) return '🍔';
    if (name.includes('sushi')) return '🍣';
    if (name.includes('salad')) return '🥗';
    if (name.includes('cake') || name.includes('dessert')) return '🍰';
    if (name.includes('taco')) return '🌮';
    if (name.includes('ramen') || name.includes('noodle')) return '🍜';
    if (name.includes('ice cream')) return '🍦';
    return '🍽️';
}

document.addEventListener('DOMContentLoaded', function () {
    // 1. Tab Navigation
    const navBtns = document.querySelectorAll('.nav-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active classes
            navBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(tc => tc.classList.remove('active'));
            
            // Add active class to clicked
            btn.classList.add('active');
            const targetId = btn.getAttribute('data-tab');
            document.getElementById(targetId).classList.add('active');
        });
    });

    // Link from Home to Analyze
    document.getElementById('go-to-analyze').addEventListener('click', () => {
        document.querySelector('.nav-btn[data-tab="tab-analyze"]').click();
    });


    // 2. Analyze Tab Logic
    const dropZone = document.getElementById('drop-zone');
    const dropContent = document.getElementById('drop-zone-content');
    const previewContainer = document.getElementById('preview-container');
    const imagePreview = document.getElementById('image-preview');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');
    const removeImage = document.getElementById('remove-image');
    
    const countSection = document.getElementById('count-section');
    const itemCount = document.getElementById('item-count');
    const countDecrease = document.getElementById('count-decrease');
    const countIncrease = document.getElementById('count-increase');
    
    const analyzeBtn = document.getElementById('analyze-btn');
    const resultsPlaceholder = document.getElementById('results-placeholder');
    const resultsDisplay = document.getElementById('results-display');
    const resultSuccess = document.getElementById('result-success');
    const resultFail = document.getElementById('result-fail');

    let selectedFile = null;

    // File Upload
    browseBtn.addEventListener('click', (e) => { e.stopPropagation(); fileInput.click(); });
    dropZone.addEventListener('click', () => { if (!selectedFile) fileInput.click(); });
    fileInput.addEventListener('change', function() { if (this.files[0]) handleFile(this.files[0]); });
    
    dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.style.borderColor = 'var(--color-caramel)'; });
    dropZone.addEventListener('dragleave', () => { dropZone.style.borderColor = 'var(--border)'; });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--border)';
        if (e.dataTransfer.files[0] && e.dataTransfer.files[0].type.startsWith('image/')) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    removeImage.addEventListener('click', (e) => {
        e.stopPropagation();
        selectedFile = null;
        fileInput.value = '';
        dropContent.style.display = 'block';
        previewContainer.style.display = 'none';
        countSection.style.display = 'none';
        analyzeBtn.disabled = true;
        
        resultsDisplay.style.display = 'none';
        resultsPlaceholder.style.display = 'flex';
    });

    function handleFile(file) {
        selectedFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            dropContent.style.display = 'none';
            previewContainer.style.display = 'block';
            countSection.style.display = 'flex';
            analyzeBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    // Counter
    countDecrease.addEventListener('click', () => {
        let v = parseInt(itemCount.value) || 1;
        if (v > 1) itemCount.value = v - 1;
    });
    countIncrease.addEventListener('click', () => {
        let v = parseInt(itemCount.value) || 1;
        if (v < 99) itemCount.value = v + 1;
    });

    // Analyze Action
    analyzeBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        const btnText = analyzeBtn.querySelector('.btn-text');
        const btnLoading = analyzeBtn.querySelector('.btn-loading');
        
        btnText.style.display = 'none';
        btnLoading.style.display = 'flex';
        analyzeBtn.disabled = true;

        const form = new FormData();
        form.append('image', selectedFile);
        const count = parseInt(itemCount.value);
        if (count > 1) form.append('item_count', count);

        try {
            const res = await fetch('/api/analyze', { method: 'POST', body: form });
            const data = await res.json();
            
            resultsPlaceholder.style.display = 'none';
            resultsDisplay.style.display = 'block';

            if (data.success && data.detected) {
                resultSuccess.style.display = 'block';
                resultFail.style.display = 'none';

                const n = data.nutrition;
                document.getElementById('food-name').textContent = n.food_name;
                document.getElementById('food-description').textContent = n.description;
                document.getElementById('confidence-value').textContent = data.confidence;
                
                animateValue('calorie-number', 0, n.total_calories, 800);
                document.getElementById('serving-value').textContent = `for ${n.serving_size} ${n.count > 1 ? '(x' + n.count + ')' : ''}`;

                document.getElementById('protein-value').textContent = n.protein_g + 'g';
                document.getElementById('carbs-value').textContent = n.carbs_g + 'g';
                document.getElementById('fat-value').textContent = n.fat_g + 'g';
                document.getElementById('fiber-value').textContent = n.fiber_g + 'g';

                if (data.note) {
                    document.getElementById('result-note').style.display = 'flex';
                    document.getElementById('note-text').textContent = data.note;
                } else {
                    document.getElementById('result-note').style.display = 'none';
                }
            } else {
                resultSuccess.style.display = 'none';
                resultFail.style.display = 'flex';
                document.getElementById('not-detected-message').textContent = data.message || "We couldn't recognize this food.";
                document.getElementById('not-detected-suggestion').textContent = data.suggestion || "Try another photo.";
            }

        } catch (err) {
            resultsPlaceholder.style.display = 'none';
            resultsDisplay.style.display = 'block';
            resultSuccess.style.display = 'none';
            resultFail.style.display = 'flex';
            document.getElementById('not-detected-message').textContent = "Connection error.";
            document.getElementById('not-detected-suggestion').textContent = "Make sure the server is running.";
        }

        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
        analyzeBtn.disabled = false;
    });

    function animateValue(id, start, end, duration) {
        const obj = document.getElementById(id);
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            obj.innerHTML = Math.floor(progress * (end - start) + start);
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }


    // 3. Foods Tab Logic
    const foodGrid = document.getElementById('food-grid');
    const searchBox = document.getElementById('food-search');
    const filterBtns = document.querySelectorAll('.filter-btn');
    let allFoods = [];
    let currentFilter = 'all';

    async function loadFoods() {
        try {
            const res = await fetch('/api/foods');
            const data = await res.json();
            if (data.success) {
                allFoods = data.foods;
                renderFoods(allFoods);
            }
        } catch (e) {
            foodGrid.innerHTML = '<div class="empty-state" style="grid-column: 1/-1;"><p>Cannot connect to server to load foods.</p></div>';
        }
    }

    function renderFoods(foods) {
        if (foods.length === 0) {
            foodGrid.innerHTML = '<div class="empty-state" style="grid-column: 1/-1;"><p>No foods found.</p></div>';
            return;
        }

        foodGrid.innerHTML = foods.map(f => {
            const emoji = getFoodEmoji(f);
            return `
            <div class="food-card" onclick="window._lookupFood('${f.key}')">
                <div class="f-icon">${emoji}</div>
                <div class="f-name">${f.name}</div>
                <div class="f-cat">${f.category.replace('_', ' ')}</div>
                <div class="f-cal">${f.calories} <span>kcal / ${f.serving_size}</span></div>
                <div class="f-macros">
                    <span class="f-mac">P: ${f.protein_g}g</span>
                    <span class="f-mac">C: ${f.carbs_g}g</span>
                    <span class="f-mac">F: ${f.fat_g}g</span>
                </div>
            </div>`;
        }).join('');
    }

    function applyFilters() {
        const query = searchBox.value.toLowerCase();
        const filtered = allFoods.filter(f => {
            const matchFilter = currentFilter === 'all' || (categories[currentFilter] || []).includes(f.category);
            const matchSearch = !query || f.name.toLowerCase().includes(query) || f.category.toLowerCase().includes(query);
            return matchFilter && matchSearch;
        });
        renderFoods(filtered);
    }

    searchBox.addEventListener('input', applyFilters);

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.getAttribute('data-filter');
            applyFilters();
        });
    });

    loadFoods();


    // 4. Modal Logic
    const modalBackdrop = document.getElementById('modal-backdrop');
    const closeModalBtn = document.getElementById('close-modal');
    const modalContent = document.getElementById('modal-content');

    window._lookupFood = async function(key) {
        try {
            const res = await fetch('/api/manual-lookup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ food_key: key })
            });
            const data = await res.json();
            if (data.success) {
                const n = data.nutrition;
                modalContent.innerHTML = `
                    <div style="text-align:center;">
                        <h2 class="food-title">${n.food_name}</h2>
                        <p class="food-subtitle mt-2">${n.description}</p>
                        <div class="cal-number mt-4" style="font-size: 56px;">${n.total_calories}</div>
                        <p class="text-sm text-muted">kcal / ${n.serving_size}</p>
                    </div>
                    <div class="macro-grid mt-4" style="margin-bottom:0;">
                        <div class="macro-item"><span class="m-label">Protein</span><span class="m-val">${n.protein_g}g</span></div>
                        <div class="macro-item"><span class="m-label">Carbs</span><span class="m-val">${n.carbs_g}g</span></div>
                        <div class="macro-item"><span class="m-label">Fat</span><span class="m-val">${n.fat_g}g</span></div>
                        <div class="macro-item"><span class="m-label">Fiber</span><span class="m-val">${n.fiber_g}g</span></div>
                    </div>
                `;
                modalBackdrop.style.display = 'flex';
            }
        } catch(e) {
            console.error("Lookup failed", e);
        }
    };

    closeModalBtn.addEventListener('click', () => {
        modalBackdrop.style.display = 'none';
    });

    modalBackdrop.addEventListener('click', (e) => {
        if (e.target === modalBackdrop) {
            modalBackdrop.style.display = 'none';
        }
    });

});
