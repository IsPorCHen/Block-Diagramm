/**
 * FlowchartRenderer - Рендерер блок-схем
 * Структура как на референсе: ветвления влево/вправо
 */
class FlowchartRenderer {
    constructor(container) {
        this.container = container;
        this.svg = null;
        this.nodePositions = new Map();
        
        // Размеры
        this.nodeWidth = 200;
        this.nodeHeight = 40;
        this.conditionSize = 50;
        this.verticalGap = 50;
        this.horizontalGap = 120;
        this.padding = 60;
        
        // Цвета (сохраняем синий дизайн)
        this.colors = {
            fill: '#dbeafe',
            stroke: '#2563eb',
            text: '#1e293b',
            startEnd: '#2563eb',
            startEndText: '#ffffff'
        };
    }
    
    render(flowchartData) {
        if (!flowchartData || !flowchartData.nodes || flowchartData.nodes.length === 0) {
            this.container.innerHTML = '<p class="no-data">Нет данных</p>';
            return;
        }
        
        this.container.innerHTML = '';
        
        const { nodes, edges } = flowchartData;
        
        // Рассчитываем позиции с учётом ветвлений
        this.calculatePositions(nodes, edges);
        
        // Определяем размеры SVG
        const bounds = this.getBounds();
        
        // Создаём SVG
        this.svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        this.svg.setAttribute('width', bounds.width);
        this.svg.setAttribute('height', bounds.height);
        this.svg.setAttribute('viewBox', `0 0 ${bounds.width} ${bounds.height}`);
        this.svg.style.display = 'block';
        
        // Маркеры стрелок
        this.addMarkers();
        
        // Рисуем связи
        edges.forEach(edge => this.drawEdge(edge, nodes));
        
        // Рисуем узлы
        nodes.forEach(node => this.drawNode(node));
        
        this.container.appendChild(this.svg);
        
        return { width: bounds.width, height: bounds.height };
    }
    
    calculatePositions(nodes, edges) {
        this.nodePositions.clear();
        
        // Строим граф
        const children = new Map();
        const parents = new Map();
        
        nodes.forEach(n => {
            children.set(n.id, []);
            parents.set(n.id, []);
        });
        
        edges.forEach(e => {
            children.get(e.from)?.push({ to: e.to, branch: e.branch, label: e.label });
            parents.get(e.to)?.push(e.from);
        });
        
        // Находим стартовый узел
        let startNode = nodes.find(n => n.type === 'start' || n.type === 'class_start');
        if (!startNode) startNode = nodes.find(n => parents.get(n.id).length === 0);
        if (!startNode && nodes.length > 0) startNode = nodes[0];
        
        // Позиционируем рекурсивно
        const visited = new Set();
        const centerX = 400;
        
        this.positionNode(startNode.id, centerX, this.padding, nodes, children, visited, 0);
    }
    
    positionNode(nodeId, x, y, nodes, children, visited, depth) {
        if (visited.has(nodeId)) return y;
        visited.add(nodeId);
        
        const node = nodes.find(n => n.id === nodeId);
        if (!node) return y;
        
        this.nodePositions.set(nodeId, { x, y });
        
        const nodeChildren = children.get(nodeId) || [];
        
        // Узел условия - ветвление влево/вправо
        if (node.type === 'condition') {
            const yesChild = nodeChildren.find(c => c.branch === 'yes');
            const noChild = nodeChildren.find(c => c.branch === 'no');
            const loopChild = nodeChildren.find(c => c.branch === 'loop');
            const otherChildren = nodeChildren.filter(c => !c.branch || c.branch === '');
            
            let maxY = y;
            
            // "да" - вниз или влево
            if (yesChild && !visited.has(yesChild.to)) {
                const yesY = this.positionNode(yesChild.to, x, y + this.verticalGap + this.conditionSize, 
                                               nodes, children, visited, depth + 1);
                maxY = Math.max(maxY, yesY);
            }
            
            // "нет" - вправо
            if (noChild && !visited.has(noChild.to)) {
                const noX = x + this.horizontalGap + this.nodeWidth / 2;
                const noY = this.positionNode(noChild.to, noX, y, nodes, children, visited, depth + 1);
                maxY = Math.max(maxY, noY);
            }
            
            // Обычные дети (выход из условия без else)
            otherChildren.forEach(child => {
                if (!visited.has(child.to)) {
                    const childY = this.positionNode(child.to, x, maxY + this.verticalGap + this.nodeHeight,
                                                     nodes, children, visited, depth + 1);
                    maxY = Math.max(maxY, childY);
                }
            });
            
            return maxY;
        }
        
        // Обычный узел - дети идут вниз
        let currentY = y;
        nodeChildren.forEach(child => {
            if (!visited.has(child.to)) {
                currentY = this.positionNode(child.to, x, currentY + this.verticalGap + this.nodeHeight,
                                             nodes, children, visited, depth + 1);
            }
        });
        
        return Math.max(y, currentY);
    }
    
    getBounds() {
        let minX = Infinity, maxX = -Infinity;
        let minY = Infinity, maxY = -Infinity;
        
        this.nodePositions.forEach(pos => {
            minX = Math.min(minX, pos.x - this.nodeWidth / 2);
            maxX = Math.max(maxX, pos.x + this.nodeWidth / 2);
            minY = Math.min(minY, pos.y - this.nodeHeight / 2);
            maxY = Math.max(maxY, pos.y + this.nodeHeight / 2);
        });
        
        // Сдвигаем все позиции чтобы начинались от padding
        const offsetX = this.padding - minX;
        const offsetY = this.padding - minY;
        
        this.nodePositions.forEach((pos, id) => {
            pos.x += offsetX;
            pos.y += offsetY;
        });
        
        return {
            width: (maxX - minX) + this.padding * 2,
            height: (maxY - minY) + this.padding * 2
        };
    }
    
    addMarkers() {
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        
        const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
        marker.setAttribute('id', 'arrow');
        marker.setAttribute('markerWidth', '10');
        marker.setAttribute('markerHeight', '10');
        marker.setAttribute('refX', '9');
        marker.setAttribute('refY', '3');
        marker.setAttribute('orient', 'auto');
        
        const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon.setAttribute('points', '0 0, 10 3, 0 6');
        polygon.setAttribute('fill', this.colors.stroke);
        
        marker.appendChild(polygon);
        defs.appendChild(marker);
        this.svg.appendChild(defs);
    }
    
    drawNode(node) {
        const pos = this.nodePositions.get(node.id);
        if (!pos) return;
        
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        
        switch (node.type) {
            case 'start':
            case 'class_start':
                this.drawTerminator(g, pos.x, pos.y, node.text, true);
                break;
            case 'end':
                this.drawEndCircle(g, pos.x, pos.y);
                break;
            case 'process':
                this.drawRectangle(g, pos.x, pos.y, node.text);
                break;
            case 'input':
            case 'output':
                this.drawParallelogram(g, pos.x, pos.y, node.text);
                break;
            case 'condition':
                this.drawDiamond(g, pos.x, pos.y, node.text);
                break;
            case 'method':
                this.drawTerminator(g, pos.x, pos.y, node.text, false);
                break;
            case 'try_start':
            case 'except':
            case 'finally':
                this.drawRectangle(g, pos.x, pos.y, node.text, true);
                break;
            default:
                this.drawRectangle(g, pos.x, pos.y, node.text);
        }
        
        this.svg.appendChild(g);
    }
    
    drawTerminator(g, x, y, text, withCircle = false) {
        // Кружок сверху
        if (withCircle) {
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', x);
            circle.setAttribute('cy', y - this.nodeHeight / 2 - 15);
            circle.setAttribute('r', 8);
            circle.setAttribute('fill', this.colors.stroke);
            g.appendChild(circle);
        }
        
        // Овал
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', x - this.nodeWidth / 2);
        rect.setAttribute('y', y - this.nodeHeight / 2);
        rect.setAttribute('width', this.nodeWidth);
        rect.setAttribute('height', this.nodeHeight);
        rect.setAttribute('rx', this.nodeHeight / 2);
        rect.setAttribute('ry', this.nodeHeight / 2);
        rect.setAttribute('fill', this.colors.fill);
        rect.setAttribute('stroke', this.colors.stroke);
        rect.setAttribute('stroke-width', '2');
        g.appendChild(rect);
        
        // Текст
        const textEl = this.createText(x, y, text);
        g.appendChild(textEl);
    }
    
    drawEndCircle(g, x, y) {
        // Внешний ромб-выход
        const size = 15;
        const outer = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        outer.setAttribute('points', `${x},${y-size} ${x+size},${y} ${x},${y+size} ${x-size},${y}`);
        outer.setAttribute('fill', 'white');
        outer.setAttribute('stroke', this.colors.stroke);
        outer.setAttribute('stroke-width', '2');
        g.appendChild(outer);
        
        // Внутренний кружок
        const inner = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        inner.setAttribute('cx', x);
        inner.setAttribute('cy', y);
        inner.setAttribute('r', 6);
        inner.setAttribute('fill', this.colors.stroke);
        g.appendChild(inner);
    }
    
    drawRectangle(g, x, y, text, dashed = false) {
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', x - this.nodeWidth / 2);
        rect.setAttribute('y', y - this.nodeHeight / 2);
        rect.setAttribute('width', this.nodeWidth);
        rect.setAttribute('height', this.nodeHeight);
        rect.setAttribute('fill', this.colors.fill);
        rect.setAttribute('stroke', this.colors.stroke);
        rect.setAttribute('stroke-width', '2');
        if (dashed) {
            rect.setAttribute('stroke-dasharray', '5,3');
        }
        g.appendChild(rect);
        
        const textEl = this.createText(x, y, text);
        g.appendChild(textEl);
    }
    
    drawParallelogram(g, x, y, text) {
        const w = this.nodeWidth / 2;
        const h = this.nodeHeight / 2;
        const skew = 15;
        
        const points = [
            `${x - w + skew},${y - h}`,
            `${x + w + skew},${y - h}`,
            `${x + w - skew},${y + h}`,
            `${x - w - skew},${y + h}`
        ].join(' ');
        
        const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        poly.setAttribute('points', points);
        poly.setAttribute('fill', this.colors.fill);
        poly.setAttribute('stroke', this.colors.stroke);
        poly.setAttribute('stroke-width', '2');
        g.appendChild(poly);
        
        const textEl = this.createText(x, y, text);
        g.appendChild(textEl);
    }
    
    drawDiamond(g, x, y, text) {
        const size = this.conditionSize;
        
        const points = [
            `${x},${y - size}`,
            `${x + size},${y}`,
            `${x},${y + size}`,
            `${x - size},${y}`
        ].join(' ');
        
        const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        poly.setAttribute('points', points);
        poly.setAttribute('fill', this.colors.fill);
        poly.setAttribute('stroke', this.colors.stroke);
        poly.setAttribute('stroke-width', '2');
        g.appendChild(poly);
        
        const textEl = this.createText(x, y, text, size * 1.8);
        g.appendChild(textEl);
    }
    
    drawEdge(edge, nodes) {
        const fromPos = this.nodePositions.get(edge.from);
        const toPos = this.nodePositions.get(edge.to);
        if (!fromPos || !toPos) return;
        
        const fromNode = nodes.find(n => n.id === edge.from);
        const toNode = nodes.find(n => n.id === edge.to);
        
        const path = this.calculatePath(fromPos, toPos, fromNode, toNode, edge);
        
        const pathEl = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        pathEl.setAttribute('d', path);
        pathEl.setAttribute('fill', 'none');
        pathEl.setAttribute('stroke', this.colors.stroke);
        pathEl.setAttribute('stroke-width', '2');
        pathEl.setAttribute('marker-end', 'url(#arrow)');
        
        this.svg.appendChild(pathEl);
        
        // Метка
        if (edge.label) {
            this.drawEdgeLabel(fromPos, toPos, edge);
        }
    }
    
    calculatePath(from, to, fromNode, toNode, edge) {
        const fromH = fromNode?.type === 'condition' ? this.conditionSize : this.nodeHeight / 2;
        const toH = toNode?.type === 'condition' ? this.conditionSize : this.nodeHeight / 2;
        const toEndH = toNode?.type === 'end' ? 15 : toH;
        
        let x1, y1, x2, y2;
        
        // Определяем точки выхода/входа
        if (edge.branch === 'yes' && fromNode?.type === 'condition') {
            // "да" - выход снизу
            x1 = from.x;
            y1 = from.y + fromH;
            x2 = to.x;
            y2 = to.y - toEndH;
            
            if (Math.abs(x1 - x2) < 10) {
                return `M ${x1} ${y1} L ${x2} ${y2}`;
            } else {
                const midY = y1 + 20;
                return `M ${x1} ${y1} L ${x1} ${midY} L ${x2} ${midY} L ${x2} ${y2}`;
            }
        } else if (edge.branch === 'no' && fromNode?.type === 'condition') {
            // "нет" - выход вправо
            x1 = from.x + this.conditionSize;
            y1 = from.y;
            x2 = to.x - this.nodeWidth / 2 - 10;
            y2 = to.y;
            
            return `M ${x1} ${y1} L ${x2} ${y1} L ${x2} ${y2} L ${to.x - this.nodeWidth / 2} ${y2}`;
        } else if (edge.branch === 'loop') {
            // Обратная связь цикла - идёт справа вверх
            x1 = from.x + this.nodeWidth / 2;
            y1 = from.y;
            x2 = to.x + this.conditionSize;
            y2 = to.y;
            
            const offset = 30;
            return `M ${x1} ${y1} L ${x1 + offset} ${y1} L ${x1 + offset} ${y2} L ${x2} ${y2}`;
        } else if (edge.branch === 'exception') {
            // Исключение - выход вправо
            x1 = from.x + this.nodeWidth / 2;
            y1 = from.y;
            x2 = to.x - this.nodeWidth / 2;
            y2 = to.y;
            
            const midX = x1 + 30;
            return `M ${x1} ${y1} L ${midX} ${y1} L ${midX} ${y2} L ${x2} ${y2}`;
        } else {
            // Обычная связь - сверху вниз
            x1 = from.x;
            y1 = from.y + fromH;
            x2 = to.x;
            y2 = to.y - toEndH;
            
            // Если начало в терминаторе с кружком, учитываем
            if (fromNode?.type === 'start' || fromNode?.type === 'class_start') {
                y1 = from.y + this.nodeHeight / 2;
            }
            
            if (Math.abs(x1 - x2) < 10) {
                return `M ${x1} ${y1} L ${x2} ${y2}`;
            } else {
                const midY = (y1 + y2) / 2;
                return `M ${x1} ${y1} L ${x1} ${midY} L ${x2} ${midY} L ${x2} ${y2}`;
            }
        }
    }
    
    drawEdgeLabel(from, to, edge) {
        let x, y;
        
        if (edge.branch === 'yes') {
            x = from.x - 15;
            y = from.y + this.conditionSize + 15;
        } else if (edge.branch === 'no') {
            x = from.x + this.conditionSize + 15;
            y = from.y - 5;
        } else if (edge.branch === 'exception') {
            x = from.x + this.nodeWidth / 2 + 10;
            y = from.y - 5;
        } else {
            x = (from.x + to.x) / 2 + 10;
            y = (from.y + to.y) / 2;
        }
        
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', x);
        text.setAttribute('y', y);
        text.setAttribute('font-family', 'Arial, sans-serif');
        text.setAttribute('font-size', '12');
        text.setAttribute('fill', this.colors.text);
        text.textContent = edge.label;
        
        this.svg.appendChild(text);
    }
    
    createText(x, y, text, maxWidth = 180) {
        const textEl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        textEl.setAttribute('x', x);
        textEl.setAttribute('y', y);
        textEl.setAttribute('text-anchor', 'middle');
        textEl.setAttribute('dominant-baseline', 'middle');
        textEl.setAttribute('font-family', 'Arial, sans-serif');
        textEl.setAttribute('font-size', '12');
        textEl.setAttribute('fill', this.colors.text);
        
        // Разбиваем на строки
        if (!text) {
            return textEl;
        }
        
        const words = text.split(' ');
        const lines = [];
        let currentLine = '';
        
        words.forEach(word => {
            const testLine = currentLine ? currentLine + ' ' + word : word;
            if (testLine.length * 7 > maxWidth && currentLine) {
                lines.push(currentLine);
                currentLine = word;
            } else {
                currentLine = testLine;
            }
        });
        if (currentLine) lines.push(currentLine);
        
        if (lines.length <= 3) {
            lines.forEach((line, i) => {
                if (lines.length === 1) {
                    textEl.textContent = line;
                } else {
                    const tspan = document.createElementNS('http://www.w3.org/2000/svg', 'tspan');
                    tspan.setAttribute('x', x);
                    tspan.setAttribute('y', y + (i - (lines.length - 1) / 2) * 14);
                    tspan.textContent = line;
                    textEl.appendChild(tspan);
                }
            });
        } else {
            textEl.textContent = text.substring(0, 25) + '...';
        }
        
        return textEl;
    }
}

window.FlowchartRenderer = FlowchartRenderer;
