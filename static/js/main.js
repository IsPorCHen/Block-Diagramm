/**
 * Основной JavaScript модуль приложения
 * Управляет загрузкой файлов и генерацией блок-схем
 */

let currentFile = null;
let currentScale = 1;

// DOM элементы
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const selectFileBtn = document.getElementById('selectFileBtn');
const generateBtn = document.getElementById('generateBtn');
const clearFileBtn = document.getElementById('clearFileBtn');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const errorAlert = document.getElementById('errorAlert');
const errorMessage = document.getElementById('errorMessage');
const flowchartSection = document.getElementById('flowchartSection');
const codeSection = document.getElementById('codeSection');
const sourceCode = document.getElementById('sourceCode');
const exportBtn = document.getElementById('exportBtn');
const zoomInBtn = document.getElementById('zoomInBtn');
const zoomOutBtn = document.getElementById('zoomOutBtn');
const resetZoomBtn = document.getElementById('resetZoomBtn');

/**
 * Инициализация обработчиков событий
 */
function initEventListeners() {
    selectFileBtn.addEventListener('click', () => fileInput.click());
    
    uploadArea.addEventListener('click', (e) => {
        if (e.target !== clearFileBtn && !fileInfo.contains(e.target)) {
            fileInput.click();
        }
    });
    
    fileInput.addEventListener('change', handleFileSelect);
    clearFileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        clearFile();
    });
    
    // Drag and Drop
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);

    // Кнопки управления
    generateBtn.addEventListener('click', generateFlowchart);
    exportBtn.addEventListener('click', exportToPNG);
    
    // Масштабирование
    zoomInBtn.addEventListener('click', () => zoom(1.2));
    zoomOutBtn.addEventListener('click', () => zoom(0.8));
    resetZoomBtn.addEventListener('click', resetZoom);
}

/**
 * Обработка выбора файла
 */
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) setFile(file);
}

/**
 * Обработка перетаскивания (drag over)
 */
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.add('dragover');
}

/**
 * Обработка выхода из зоны перетаскивания
 */
function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.remove('dragover');
}

/**
 * Обработка сброса файла (drop)
 */
function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.remove('dragover');
    
    const file = e.dataTransfer.files[0];
    if (file) setFile(file);
}

/**
 * Установка выбранного файла
 */
function setFile(file) {
    if (!file.name.endsWith('.py')) {
        showError('Пожалуйста, выберите файл с расширением .py');
        return;
    }
    
    if (file.size > 1024 * 1024) {
        showError('Файл слишком большой. Максимальный размер: 1 МБ');
        return;
    }
    
    currentFile = file;
    fileName.textContent = file.name;
    fileInfo.style.display = 'flex';
    document.querySelector('.upload-content').style.display = 'none';
    generateBtn.disabled = false;
    hideError();
}

/**
 * Очистка выбранного файла
 */
function clearFile() {
    currentFile = null;
    fileInput.value = '';
    fileInfo.style.display = 'none';
    document.querySelector('.upload-content').style.display = 'block';
    generateBtn.disabled = true;
    flowchartSection.style.display = 'none';
    codeSection.style.display = 'none';
}

/**
 * Генерация блок-схемы
 */
async function generateFlowchart() {
    if (!currentFile) return;

    generateBtn.disabled = true;
    document.querySelector('.btn-text').style.display = 'none';
    document.querySelector('.loader').style.display = 'block';
    hideError();
    
    const formData = new FormData();
    formData.append('file', currentFile);
    
    try {
        console.log('📤 Отправка файла на сервер...');
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Ошибка при генерации блок-схемы');
        }
        
        console.log('📥 Данные получены:', data);

        const wrapper = document.getElementById('flowchartWrapper');
        wrapper.innerHTML = '';

        // Отрисовка основной блок-схемы
        if (data.main_flowchart && data.main_flowchart.nodes && data.main_flowchart.nodes.length > 0) {
            renderFlowchart('main', 'Основной алгоритм', data.main_flowchart);
        }

        // Отрисовка блок-схем функций
        if (data.functions && data.functions.length > 0) {
            data.functions.forEach(func => {
                if (func.flowchart && func.flowchart.nodes && func.flowchart.nodes.length > 0) {
                    renderFlowchart(`func-${func.name}`, `Функция: ${func.name}`, func.flowchart);
                }
            });
        }

        // Показываем исходный код
        sourceCode.textContent = data.code;
        codeSection.style.display = 'block';
        
        flowchartSection.style.display = 'block';
        resetZoom();
        flowchartSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        console.log('✅ Генерация завершена!');
        
    } catch (error) {
        console.error('❌ Ошибка генерации:', error);
        showError(error.message);
    } finally {
        generateBtn.disabled = false;
        document.querySelector('.btn-text').style.display = 'inline';
        document.querySelector('.loader').style.display = 'none';
    }
}

/**
 * Отрисовка блок-схемы
 */
function renderFlowchart(id, title, flowchartData) {
    const wrapper = document.getElementById('flowchartWrapper');

    const section = document.createElement('div');
    section.className = 'flowchart-section-item';
    section.innerHTML = `
        <h3 class="section-title">${title}</h3>
        <div id="flowchart-${id}" class="flowchart-container-inner"></div>
    `;
    
    wrapper.appendChild(section);
    
    const renderer = new FlowchartRenderer(`flowchart-${id}`);
    renderer.render(flowchartData);
    
    const nodeCount = flowchartData.nodes ? flowchartData.nodes.length : 0;
    const edgeCount = flowchartData.edges ? flowchartData.edges.length : 0;
    console.log(`✅ Отрисована блок-схема: ${title} (${nodeCount} узлов, ${edgeCount} связей)`);
}

/**
 * Масштабирование
 */
function zoom(factor) {
    currentScale *= factor;
    currentScale = Math.max(0.3, Math.min(currentScale, 3));
    applyZoom();
}

/**
 * Сброс масштаба
 */
function resetZoom() {
    currentScale = 1;
    applyZoom();
}

/**
 * Применение масштаба
 */
function applyZoom() {
    const wrapper = document.getElementById('flowchartWrapper');
    wrapper.style.transform = `scale(${currentScale})`;
    wrapper.style.transformOrigin = 'top center';
}

/**
 * Экспорт в PNG
 */
async function exportToPNG() {
    try {
        exportBtn.disabled = true;
        exportBtn.textContent = 'Экспортирование...';

        const svgElement = document.querySelector('#flowchartWrapper svg');
        if (!svgElement) {
            throw new Error('Блок-схема не найдена');
        }
        
        // Получаем размеры SVG
        const viewBox = svgElement.getAttribute('viewBox');
        const [, , vbWidth, vbHeight] = viewBox ? viewBox.split(' ').map(Number) : [0, 0, 800, 600];
        
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        const scale = 2; // Увеличиваем для лучшего качества
        const padding = 40;
        
        canvas.width = (vbWidth + padding * 2) * scale;
        canvas.height = (vbHeight + padding * 2) * scale;
        
        ctx.scale(scale, scale);
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Клонируем SVG и настраиваем
        const svgClone = svgElement.cloneNode(true);
        svgClone.setAttribute('width', vbWidth);
        svgClone.setAttribute('height', vbHeight);
        
        const svgString = new XMLSerializer().serializeToString(svgClone);
        const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
        const url = URL.createObjectURL(svgBlob);

        const img = new Image();
        img.onload = function() {
            ctx.drawImage(img, padding, padding);
            URL.revokeObjectURL(url);
            
            canvas.toBlob(function(blob) {
                const link = document.createElement('a');
                link.download = `flowchart_${Date.now()}.png`;
                link.href = URL.createObjectURL(blob);
                link.click();
                URL.revokeObjectURL(link.href);
                
                resetExportBtn();
            });
        };
        
        img.onerror = function() {
            URL.revokeObjectURL(url);
            throw new Error('Ошибка загрузки изображения');
        };
        
        img.src = url;
        
    } catch (error) {
        showError('Ошибка при экспорте: ' + error.message);
        resetExportBtn();
    }
}

/**
 * Сброс кнопки экспорта
 */
function resetExportBtn() {
    exportBtn.disabled = false;
    exportBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
        </svg>
        Экспортировать в PNG
    `;
}

/**
 * Показать ошибку
 */
function showError(message) {
    errorMessage.textContent = message;
    errorAlert.style.display = 'flex';
    errorAlert.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

/**
 * Скрыть ошибку
 */
function hideError() {
    errorAlert.style.display = 'none';
}

/**
 * Закрыть alert
 */
function closeAlert() {
    hideError();
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Приложение загружено');
    initEventListeners();
});
