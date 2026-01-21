/**
 * FlowchartRenderer - Рендерер блок-схем с поддержкой ветвлений и циклов
 * Использует алгоритм размещения узлов на основе уровней (layers)
 */
class FlowchartRenderer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.blockWidth = 160;
        this.blockHeight = 50;
        this.conditionSize = 70;
        this.verticalGap = 60;
        this.horizontalGap = 80;
        this.padding = 50;
        
        // Цвета по ГОСТ
        this.colors = {
            fill: '#dbeafe',
            stroke: '#2563eb',
            text: '#1e293b',
            arrow: '#2563eb',
            labelBg: '#ffffff',
            yesColor: '#10b981',
            noColor: '#ef4444'
        };
    }
    
    render(flowchartData) {
        if (!flowchartData || !flowchartData.nodes || flowchartData.nodes.length === 0) {
            this.container.innerHTML = '<p style="text-align: center; color: #666;">Нет данных для отображения</p>';
            return;
        }
        
        this.container.innerHTML = '';
        
        const { nodes, edges } = flowchartData;
        
        // Вычисляем позиции узлов
        const layout = this.calculateLayout(nodes, edges);
        
        // Создаём SVG
        const svg = this.createSVG(layout);
        
        // Добавляем маркер стрелки
        this.addArrowMarker(svg);
        
        // Рисуем связи (сначала, чтобы были под узлами)
        edges.forEach(edge => {
            this.drawEdge(svg, edge, layout);
        });
        
        // Рисуем узлы
        nodes.forEach(node => {
            this.drawNode(svg, node, layout);
        });
        
        this.container.appendChild(svg);
    }
    
    calculateLayout(nodes, edges) {
        // Строим граф смежности
        const adjacency = new Map();
        const reverseAdj = new Map();
        
        nodes.forEach(node => {
            adjacency.set(node.id, []);
            reverseAdj.set(node.id, []);
        });
        
        edges.forEach(edge => {
            if (adjacency.has(edge.from)) {
                adjacency.get(edge.from).push(edge.to);
            }
            if (reverseAdj.has(edge.to)) {
                reverseAdj.get(edge.to).push(edge.from);
            }
        });
        
        // Топологическая сортировка с учётом уровней
        const levels = this.assignLevels(nodes, adjacency, reverseAdj);
        
        // Группируем узлы по уровням
        const levelGroups = new Map();
        nodes.forEach(node => {
            const level = levels.get(node.id) || 0;
            if (!levelGroups.has(level)) {
                levelGroups.set(level, []);
            }
            levelGroups.get(level).push(node);
        });
        
        // Сортируем уровни
        const sortedLevels = Array.from(levelGroups.keys()).sort((a, b) => a - b);
        
        // Вычисляем максимальную ширину уровня
        let maxLevelWidth = 0;
        sortedLevels.forEach(level => {
            const nodesAtLevel = levelGroups.get(level);
            maxLevelWidth = Math.max(maxLevelWidth, nodesAtLevel.length);
        });
        
        // Вычисляем позиции
        const positions = new Map();
        const totalWidth = maxLevelWidth * (this.blockWidth + this.horizontalGap);
        
        sortedLevels.forEach((level, levelIndex) => {
            const nodesAtLevel = levelGroups.get(level);
            const levelWidth = nodesAtLevel.length * (this.blockWidth + this.horizontalGap) - this.horizontalGap;
            const startX = this.padding + (totalWidth - levelWidth) / 2;
            
            nodesAtLevel.forEach((node, nodeIndex) => {
                const x = startX + nodeIndex * (this.blockWidth + this.horizontalGap) + this.blockWidth / 2;
                const y = this.padding + levelIndex * (this.blockHeight + this.verticalGap) + this.blockHeight / 2;
                positions.set(node.id, { x, y, level: levelIndex });
            });
        });
        
        // Определяем размеры SVG
        const width = totalWidth + this.padding * 2;
        const height = sortedLevels.length * (this.blockHeight + this.verticalGap) + this.padding * 2;
        
        return { positions, width, height, nodes, edges };
    }
    
    assignLevels(nodes, adjacency, reverseAdj) {
        const levels = new Map();
        const visited = new Set();
        
        // Находим начальный узел (без входящих рёбер или типа 'start')
        let startNode = nodes.find(n => n.type === 'start');
        if (!startNode) {
            startNode = nodes.find(n => reverseAdj.get(n.id).length === 0);
        }
        if (!startNode && nodes.length > 0) {
            startNode = nodes[0];
        }
        
        // BFS для назначения уровней
        const queue = [];
        if (startNode) {
            queue.push({ id: startNode.id, level: 0 });
            levels.set(startNode.id, 0);
        }
        
        while (queue.length > 0) {
            const { id, level } = queue.shift();
            
            if (visited.has(id)) {
                // Обновляем уровень если нашли более длинный путь
                if (levels.get(id) < level) {
                    levels.set(id, level);
                }
                continue;
            }
            
            visited.add(id);
            levels.set(id, level);
            
            const neighbors = adjacency.get(id) || [];
            neighbors.forEach(neighborId => {
                const currentLevel = levels.get(neighborId);
                const newLevel = level + 1;
                
                if (currentLevel === undefined || currentLevel < newLevel) {
                    levels.set(neighborId, newLevel);
                    queue.push({ id: neighborId, level: newLevel });
                }
            });
        }
        
        // Обрабатываем непосещённые узлы
        nodes.forEach(node => {
            if (!levels.has(node.id)) {
                levels.set(node.id, 0);
            }
        });
        
        return levels;
    }
    
    createSVG(layout) {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '100%');
        svg.setAttribute('height', layout.height);
        svg.setAttribute('viewBox', `0 0 ${layout.width} ${layout.height}`);
        svg.style.display = 'block';
        svg.style.margin = '0 auto';
        svg.style.minWidth = `${layout.width}px`;
        return svg;
    }
    
    addArrowMarker(svg) {
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        
        // Обычная стрелка
        const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
        marker.setAttribute('id', 'arrowhead');
        marker.setAttribute('markerWidth', '10');
        marker.setAttribute('markerHeight', '10');
        marker.setAttribute('refX', '9');
        marker.setAttribute('refY', '3');
        marker.setAttribute('orient', 'auto');
        marker.setAttribute('markerUnits', 'strokeWidth');
        
        const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon.setAttribute('points', '0 0, 10 3, 0 6');
        polygon.setAttribute('fill', this.colors.arrow);
        
        marker.appendChild(polygon);
        defs.appendChild(marker);
        
        // Зелёная стрелка (Да)
        const markerYes = marker.cloneNode(true);
        markerYes.setAttribute('id', 'arrowhead-yes');
        markerYes.querySelector('polygon').setAttribute('fill', this.colors.yesColor);
        defs.appendChild(markerYes);
        
        // Красная стрелка (Нет)
        const markerNo = marker.cloneNode(true);
        markerNo.setAttribute('id', 'arrowhead-no');
        markerNo.querySelector('polygon').setAttribute('fill', this.colors.noColor);
        defs.appendChild(markerNo);
        
        svg.appendChild(defs);
    }
    
    drawNode(svg, node, layout) {
        const pos = layout.positions.get(node.id);
        if (!pos) return;
        
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.setAttribute('class', `node node-${node.type}`);
        
        switch (node.type) {
            case 'start':
            case 'end':
                this.drawTerminal(group, pos.x, pos.y, node.text);
                break;
            case 'operation':
                this.drawProcess(group, pos.x, pos.y, node.text);
                break;
            case 'input':
            case 'output':
                this.drawIO(group, pos.x, pos.y, node.text);
                break;
            case 'condition':
            case 'loop_condition':
                this.drawDecision(group, pos.x, pos.y, node.text);
                break;
            case 'loop_init':
                this.drawLoopInit(group, pos.x, pos.y, node.text);
                break;
            default:
                this.drawProcess(group, pos.x, pos.y, node.text);
        }
        
        svg.appendChild(group);
    }
    
    drawTerminal(group, x, y, text) {
        // Овал для начала/конца
        const ellipse = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
        ellipse.setAttribute('cx', x);
        ellipse.setAttribute('cy', y);
        ellipse.setAttribute('rx', this.blockWidth / 2);
        ellipse.setAttribute('ry', this.blockHeight / 2);
        ellipse.setAttribute('fill', this.colors.fill);
        ellipse.setAttribute('stroke', this.colors.stroke);
        ellipse.setAttribute('stroke-width', '2');
        
        const textEl = this.createText(x, y, text);
        
        group.appendChild(ellipse);
        group.appendChild(textEl);
    }
    
    drawProcess(group, x, y, text) {
        // Прямоугольник для действия
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', x - this.blockWidth / 2);
        rect.setAttribute('y', y - this.blockHeight / 2);
        rect.setAttribute('width', this.blockWidth);
        rect.setAttribute('height', this.blockHeight);
        rect.setAttribute('fill', this.colors.fill);
        rect.setAttribute('stroke', this.colors.stroke);
        rect.setAttribute('stroke-width', '2');
        rect.setAttribute('rx', '4');
        
        const textEl = this.createText(x, y, text);
        
        group.appendChild(rect);
        group.appendChild(textEl);
    }
    
    drawIO(group, x, y, text) {
        // Параллелограмм для ввода/вывода
        const offset = 15;
        const points = [
            [x - this.blockWidth / 2 + offset, y - this.blockHeight / 2],
            [x + this.blockWidth / 2 + offset, y - this.blockHeight / 2],
            [x + this.blockWidth / 2 - offset, y + this.blockHeight / 2],
            [x - this.blockWidth / 2 - offset, y + this.blockHeight / 2]
        ];
        
        const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon.setAttribute('points', points.map(p => p.join(',')).join(' '));
        polygon.setAttribute('fill', this.colors.fill);
        polygon.setAttribute('stroke', this.colors.stroke);
        polygon.setAttribute('stroke-width', '2');
        
        const textEl = this.createText(x, y, text);
        
        group.appendChild(polygon);
        group.appendChild(textEl);
    }
    
    drawDecision(group, x, y, text) {
        // Ромб для условия
        const size = this.conditionSize;
        const points = [
            [x, y - size],
            [x + size, y],
            [x, y + size],
            [x - size, y]
        ];
        
        const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon.setAttribute('points', points.map(p => p.join(',')).join(' '));
        polygon.setAttribute('fill', this.colors.fill);
        polygon.setAttribute('stroke', this.colors.stroke);
        polygon.setAttribute('stroke-width', '2');
        
        const textEl = this.createText(x, y, text, size * 1.5);
        
        group.appendChild(polygon);
        group.appendChild(textEl);
    }
    
    drawLoopInit(group, x, y, text) {
        // Шестиугольник для подготовки цикла
        const w = this.blockWidth / 2;
        const h = this.blockHeight / 2;
        const cut = 15;
        
        const points = [
            [x - w + cut, y - h],
            [x + w - cut, y - h],
            [x + w, y],
            [x + w - cut, y + h],
            [x - w + cut, y + h],
            [x - w, y]
        ];
        
        const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon.setAttribute('points', points.map(p => p.join(',')).join(' '));
        polygon.setAttribute('fill', this.colors.fill);
        polygon.setAttribute('stroke', this.colors.stroke);
        polygon.setAttribute('stroke-width', '2');
        
        const textEl = this.createText(x, y, text);
        
        group.appendChild(polygon);
        group.appendChild(textEl);
    }
    
    drawEdge(svg, edge, layout) {
        const fromPos = layout.positions.get(edge.from);
        const toPos = layout.positions.get(edge.to);
        
        if (!fromPos || !toPos) return;
        
        const fromNode = layout.nodes.find(n => n.id === edge.from);
        const toNode = layout.nodes.find(n => n.id === edge.to);
        
        // Определяем точки соединения
        const points = this.calculateEdgePoints(fromPos, toPos, fromNode, toNode, edge.label);
        
        // Определяем цвет и маркер
        let strokeColor = this.colors.arrow;
        let markerId = 'arrowhead';
        
        if (edge.label === 'Да') {
            strokeColor = this.colors.yesColor;
            markerId = 'arrowhead-yes';
        } else if (edge.label === 'Нет') {
            strokeColor = this.colors.noColor;
            markerId = 'arrowhead-no';
        }
        
        // Рисуем путь
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', this.pointsToPath(points));
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke', strokeColor);
        path.setAttribute('stroke-width', '2');
        path.setAttribute('marker-end', `url(#${markerId})`);
        
        svg.appendChild(path);
        
        // Добавляем метку
        if (edge.label) {
            this.drawEdgeLabel(svg, points, edge.label, strokeColor);
        }
    }
    
    calculateEdgePoints(fromPos, toPos, fromNode, toNode, label) {
        const points = [];
        
        // Определяем размеры узлов
        const fromHeight = (fromNode && (fromNode.type === 'condition' || fromNode.type === 'loop_condition')) 
            ? this.conditionSize : this.blockHeight / 2;
        const toHeight = (toNode && (toNode.type === 'condition' || toNode.type === 'loop_condition')) 
            ? this.conditionSize : this.blockHeight / 2;
        const fromWidth = (fromNode && (fromNode.type === 'condition' || fromNode.type === 'loop_condition')) 
            ? this.conditionSize : this.blockWidth / 2;
        const toWidth = (toNode && (toNode.type === 'condition' || toNode.type === 'loop_condition')) 
            ? this.conditionSize : this.blockWidth / 2;
        
        // Определяем направление
        const dx = toPos.x - fromPos.x;
        const dy = toPos.y - fromPos.y;
        
        // Проверяем, идёт ли линия обратно вверх (цикл)
        const isBackEdge = dy < 0;
        
        if (isBackEdge) {
            // Обратная связь цикла - рисуем сбоку
            const offset = this.horizontalGap / 2 + 20;
            
            points.push({ x: fromPos.x + fromWidth, y: fromPos.y });
            points.push({ x: fromPos.x + fromWidth + offset, y: fromPos.y });
            points.push({ x: fromPos.x + fromWidth + offset, y: toPos.y });
            points.push({ x: toPos.x + toWidth, y: toPos.y });
        } else if (Math.abs(dx) < 10) {
            // Вертикальная связь
            points.push({ x: fromPos.x, y: fromPos.y + fromHeight });
            points.push({ x: toPos.x, y: toPos.y - toHeight });
        } else if (fromNode && (fromNode.type === 'condition' || fromNode.type === 'loop_condition')) {
            // Связь от условия - выходим сбоку
            if (label === 'Да') {
                // Да - выходим снизу
                points.push({ x: fromPos.x, y: fromPos.y + fromHeight });
                if (Math.abs(dx) > 10) {
                    points.push({ x: fromPos.x, y: (fromPos.y + toPos.y) / 2 });
                    points.push({ x: toPos.x, y: (fromPos.y + toPos.y) / 2 });
                }
                points.push({ x: toPos.x, y: toPos.y - toHeight });
            } else if (label === 'Нет') {
                // Нет - выходим вправо
                points.push({ x: fromPos.x + fromWidth, y: fromPos.y });
                points.push({ x: toPos.x + toWidth + 30, y: fromPos.y });
                points.push({ x: toPos.x + toWidth + 30, y: toPos.y });
                points.push({ x: toPos.x + toWidth, y: toPos.y });
            } else {
                // Обычная связь
                points.push({ x: fromPos.x, y: fromPos.y + fromHeight });
                if (Math.abs(dx) > 10) {
                    points.push({ x: fromPos.x, y: (fromPos.y + toPos.y) / 2 });
                    points.push({ x: toPos.x, y: (fromPos.y + toPos.y) / 2 });
                }
                points.push({ x: toPos.x, y: toPos.y - toHeight });
            }
        } else {
            // Обычная связь с изгибом
            points.push({ x: fromPos.x, y: fromPos.y + fromHeight });
            
            if (Math.abs(dx) > 10) {
                const midY = (fromPos.y + fromHeight + toPos.y - toHeight) / 2;
                points.push({ x: fromPos.x, y: midY });
                points.push({ x: toPos.x, y: midY });
            }
            
            points.push({ x: toPos.x, y: toPos.y - toHeight });
        }
        
        return points;
    }
    
    pointsToPath(points) {
        if (points.length < 2) return '';
        
        let d = `M ${points[0].x} ${points[0].y}`;
        
        for (let i = 1; i < points.length; i++) {
            d += ` L ${points[i].x} ${points[i].y}`;
        }
        
        return d;
    }
    
    drawEdgeLabel(svg, points, label, color) {
        // Находим середину пути для размещения метки
        let labelX, labelY;
        
        if (points.length === 2) {
            labelX = (points[0].x + points[1].x) / 2;
            labelY = (points[0].y + points[1].y) / 2;
        } else {
            // Размещаем у начала второго сегмента
            labelX = points[1].x + 5;
            labelY = points[0].y + 15;
        }
        
        // Фон для метки
        const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        bg.setAttribute('x', labelX - 12);
        bg.setAttribute('y', labelY - 10);
        bg.setAttribute('width', 24);
        bg.setAttribute('height', 16);
        bg.setAttribute('fill', this.colors.labelBg);
        bg.setAttribute('rx', '3');
        
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', labelX);
        text.setAttribute('y', labelY + 2);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('dominant-baseline', 'middle');
        text.setAttribute('font-family', 'Arial, sans-serif');
        text.setAttribute('font-size', '11');
        text.setAttribute('font-weight', 'bold');
        text.setAttribute('fill', color);
        text.textContent = label;
        
        svg.appendChild(bg);
        svg.appendChild(text);
    }
    
    createText(x, y, text, maxWidth = 150) {
        const textEl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        textEl.setAttribute('x', x);
        textEl.setAttribute('y', y);
        textEl.setAttribute('text-anchor', 'middle');
        textEl.setAttribute('dominant-baseline', 'middle');
        textEl.setAttribute('font-family', 'Arial, sans-serif');
        textEl.setAttribute('font-size', '11');
        textEl.setAttribute('fill', this.colors.text);
        
        // Разбиваем текст на строки
        const words = text.split(' ');
        const lines = [];
        let currentLine = '';
        
        words.forEach(word => {
            const testLine = currentLine ? currentLine + ' ' + word : word;
            if (testLine.length * 6.5 > maxWidth) {
                if (currentLine) lines.push(currentLine);
                currentLine = word;
            } else {
                currentLine = testLine;
            }
        });
        if (currentLine) lines.push(currentLine);
        
        // Ограничиваем до 3 строк
        if (lines.length > 3) {
            lines.length = 3;
            lines[2] = lines[2].substring(0, lines[2].length - 3) + '...';
        }
        
        if (lines.length === 1) {
            textEl.textContent = text.length > 25 ? text.substring(0, 22) + '...' : text;
        } else {
            const lineHeight = 14;
            const startY = y - ((lines.length - 1) * lineHeight) / 2;
            
            lines.forEach((line, index) => {
                const tspan = document.createElementNS('http://www.w3.org/2000/svg', 'tspan');
                tspan.setAttribute('x', x);
                tspan.setAttribute('y', startY + index * lineHeight);
                tspan.textContent = line.length > 20 ? line.substring(0, 17) + '...' : line;
                textEl.appendChild(tspan);
            });
        }
        
        return textEl;
    }
}

window.FlowchartRenderer = FlowchartRenderer;
