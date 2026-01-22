let currentFile = null;
const flowchartInstances = new Map();

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
    
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    generateBtn.addEventListener('click', generateFlowchart);
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) setFile(file);
}

function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) setFile(file);
}

function setFile(file) {
    if (!file.name.endsWith('.py')) {
        showError('Пожалуйста, выберите файл .py');
        return;
    }
    
    if (file.size > 1024 * 1024) {
        showError('Файл слишком большой (макс. 1 МБ)');
        return;
    }
    
    currentFile = file;
    fileName.textContent = file.name;
    fileInfo.style.display = 'flex';
    document.querySelector('.upload-content').style.display = 'none';
    generateBtn.disabled = false;
    hideError();
}

function clearFile() {
    currentFile = null;
    fileInput.value = '';
    fileInfo.style.display = 'none';
    document.querySelector('.upload-content').style.display = 'block';
    generateBtn.disabled = true;
    flowchartSection.style.display = 'none';
    codeSection.style.display = 'none';
    flowchartInstances.clear();
}

async function generateFlowchart() {
    if (!currentFile) return;

    generateBtn.disabled = true;
    document.querySelector('.btn-text').style.display = 'none';
    document.querySelector('.loader').style.display = 'block';
    hideError();
    
    const formData = new FormData();
    formData.append('file', currentFile);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Ошибка генерации');
        }

        const wrapper = document.getElementById('flowchartWrapper');
        wrapper.innerHTML = '';
        flowchartInstances.clear();

        // Основная блок-схема
        if (data.main_flowchart?.nodes?.length > 0) {
            createFlowchartPanel('main', 'Основной алгоритм', data.main_flowchart);
        }

        // Классы
        if (data.classes?.length > 0) {
            data.classes.forEach(cls => {
                if (cls.flowchart?.nodes?.length > 0) {
                    createFlowchartPanel(`class-${cls.name}`, `Класс: ${cls.name}`, cls.flowchart);
                }
            });
        }

        // Функции и методы
        if (data.functions?.length > 0) {
            data.functions.forEach(func => {
                if (func.flowchart?.nodes?.length > 0) {
                    const title = func.type === 'method' 
                        ? `Метод: ${func.name}` 
                        : `Функция: ${func.name}`;
                    createFlowchartPanel(`func-${func.name}`, title, func.flowchart);
                }
            });
        }

        // Код
        sourceCode.textContent = data.code;
        codeSection.style.display = 'block';
        
        flowchartSection.style.display = 'block';
        flowchartSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
    } catch (error) {
        console.error('Ошибка:', error);
        showError(error.message);
    } finally {
        generateBtn.disabled = false;
        document.querySelector('.btn-text').style.display = 'inline';
        document.querySelector('.loader').style.display = 'none';
    }
}

function createFlowchartPanel(id, title, flowchartData) {
    const wrapper = document.getElementById('flowchartWrapper');
    
    const panel = document.createElement('div');
    panel.className = 'flowchart-panel';
    panel.innerHTML = `
        <div class="panel-header">
            <h3 class="panel-title">${title}</h3>
            <div class="panel-controls">
                <button class="btn-icon" title="Увеличить" data-action="zoom-in">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                        <line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/>
                    </svg>
                </button>
                <button class="btn-icon" title="Уменьшить" data-action="zoom-out">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                        <line x1="8" y1="11" x2="14" y2="11"/>
                    </svg>
                </button>
                <button class="btn-icon" title="Сбросить" data-action="reset">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                        <path d="M3 3v5h5"/>
                    </svg>
                </button>
                <button class="btn-icon btn-download" title="Скачать PNG" data-action="download">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="7 10 12 15 17 10"/>
                        <line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>
                </button>
            </div>
        </div>
        <div class="panel-viewport" id="viewport-${id}">
            <div class="panel-content" id="content-${id}">
                <div class="flowchart-container" id="flowchart-${id}"></div>
            </div>
        </div>
        <div class="panel-zoom-info" id="zoom-info-${id}">100%</div>
    `;
    
    wrapper.appendChild(panel);
    
    // Рендер блок-схемы
    const container = document.getElementById(`flowchart-${id}`);
    const renderer = new FlowchartRenderer(container);
    const size = renderer.render(flowchartData);
    
    // Сохраняем состояние
    const state = {
        id,
        title,
        scale: 1,
        panX: 0,
        panY: 0,
        isPanning: false,
        startX: 0,
        startY: 0,
        renderer,
        size
    };
    flowchartInstances.set(id, state);
    
    setupPanelInteraction(panel, state);
}

function setupPanelInteraction(panel, state) {
    const viewport = panel.querySelector('.panel-viewport');
    const content = panel.querySelector('.panel-content');
    const zoomInfo = panel.querySelector('.panel-zoom-info');
    
    // Кнопки управления
    panel.querySelectorAll('.btn-icon').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const action = btn.dataset.action;
            switch (action) {
                case 'zoom-in':
                    zoom(state, 1.2, content, zoomInfo);
                    break;
                case 'zoom-out':
                    zoom(state, 0.8, content, zoomInfo);
                    break;
                case 'reset':
                    resetView(state, content, zoomInfo);
                    break;
                case 'download':
                    downloadFlowchart(state);
                    break;
            }
        });
    });
    
    // Масштабирование колёсиком
    viewport.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        zoom(state, delta, content, zoomInfo);
    }, { passive: false });
    
    // Перетаскивание ЛКМ
    viewport.addEventListener('mousedown', (e) => {
        if (e.button === 0) {
            state.isPanning = true;
            state.startX = e.clientX - state.panX;
            state.startY = e.clientY - state.panY;
            viewport.style.cursor = 'grabbing';
        }
    });
    
    document.addEventListener('mousemove', (e) => {
        if (state.isPanning) {
            state.panX = e.clientX - state.startX;
            state.panY = e.clientY - state.startY;
            updateTransform(state, content);
        }
    });
    
    document.addEventListener('mouseup', () => {
        if (state.isPanning) {
            state.isPanning = false;
            viewport.style.cursor = 'grab';
        }
    });
    
    viewport.style.cursor = 'grab';
}

function zoom(state, factor, content, zoomInfo) {
    state.scale *= factor;
    state.scale = Math.max(0.2, Math.min(state.scale, 5));
    updateTransform(state, content);
    zoomInfo.textContent = Math.round(state.scale * 100) + '%';
}

function resetView(state, content, zoomInfo) {
    state.scale = 1;
    state.panX = 0;
    state.panY = 0;
    updateTransform(state, content);
    zoomInfo.textContent = '100%';
}

function updateTransform(state, content) {
    content.style.transform = `translate(${state.panX}px, ${state.panY}px) scale(${state.scale})`;
}

async function downloadFlowchart(state) {
    try {
        const container = document.getElementById(`flowchart-${state.id}`);
        const svgElement = container.querySelector('svg');
        if (!svgElement) {
            showError('Блок-схема не найдена');
            return;
        }

        const svgClone = svgElement.cloneNode(true);
        const viewBox = svgElement.getAttribute('viewBox');
        const [, , width, height] = viewBox ? viewBox.split(' ').map(Number) : [0, 0, 800, 600];
        
        svgClone.setAttribute('width', width);
        svgClone.setAttribute('height', height);

        const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        bg.setAttribute('width', '100%');
        bg.setAttribute('height', '100%');
        bg.setAttribute('fill', 'white');
        svgClone.insertBefore(bg, svgClone.firstChild);
        
        const svgString = new XMLSerializer().serializeToString(svgClone);
        const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
        const url = URL.createObjectURL(svgBlob);
        
        const img = new Image();
        img.onload = () => {
            const canvas = document.createElement('canvas');
            const scale = 2;
            canvas.width = width * scale;
            canvas.height = height * scale;
            
            const ctx = canvas.getContext('2d');
            ctx.scale(scale, scale);
            ctx.fillStyle = 'white';
            ctx.fillRect(0, 0, width, height);
            ctx.drawImage(img, 0, 0);
            
            URL.revokeObjectURL(url);
            
            canvas.toBlob((blob) => {
                const link = document.createElement('a');
                link.download = `flowchart_${state.title.replace(/[^a-zA-Zа-яА-Я0-9]/g, '_')}.png`;
                link.href = URL.createObjectURL(blob);
                link.click();
                URL.revokeObjectURL(link.href);
            });
        };
        
        img.src = url;
        
    } catch (error) {
        showError('Ошибка скачивания: ' + error.message);
    }
}

function showError(message) {
    errorMessage.textContent = message;
    errorAlert.style.display = 'flex';
}

function hideError() {
    errorAlert.style.display = 'none';
}

function closeAlert() {
    hideError();
}

document.addEventListener('DOMContentLoaded', initEventListeners);
