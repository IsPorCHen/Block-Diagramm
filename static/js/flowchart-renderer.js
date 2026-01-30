/**
 * FlowchartRenderer - Рендерер блок-схем
 * 
 * Все стрелки входят в блоки СВЕРХУ с видимым вертикальным сегментом
 * Циклы: шестиугольник, выход СПРАВА, обратная связь СЛЕВА
 * Условия: ромб, "да" вниз, "нет" вправо
 */
class FlowchartRenderer {
    constructor(container) {
        this.container = container;
        this.svg = null;
        this.nodePositions = new Map();
        
        // Размеры
        this.nodeWidth = 180;
        this.nodeHeight = 40;
        this.conditionSize = 45;
        this.hexWidth = 180;
        this.hexHeight = 40;
        this.verticalGap = 70;  // Увеличен
        this.horizontalGap = 130;
        this.padding = 80;
        this.loopLeftOffset = 50;
        this.arrowGap = 25; // Минимальный отступ для стрелок
        
        // Цвета
        this.colors = {
            fill: '#dbeafe',
            stroke: '#2563eb',
            text: '#1e293b'
        };
    }
    
    render(flowchartData) {
        if (!flowchartData || !flowchartData.nodes || flowchartData.nodes.length === 0) {
            this.container.innerHTML = '<p class="no-data">Нет данных</p>';
            return { width: 400, height: 200 };
        }
        
        this.container.innerHTML = '';
        this.nodePositions.clear();
        
        const { nodes, edges } = flowchartData;
        
        this.buildGraph(nodes, edges);
        
        const isClassDiagram = nodes.some(n => n.type === 'class_start');
        
        if (isClassDiagram) {
            this.calculateClassPositions(nodes, edges);
        } else {
            this.calculatePositions(nodes, edges);
        }
        
        const bounds = this.getBounds(nodes);
        
        this.svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        this.svg.setAttribute('width', bounds.width);
        this.svg.setAttribute('height', bounds.height);
        this.svg.setAttribute('viewBox', `0 0 ${bounds.width} ${bounds.height}`);
        
        this.addArrowMarker();
        
        edges.forEach(edge => this.drawEdge(edge, nodes));
        nodes.forEach(node => this.drawNode(node));
        
        this.container.appendChild(this.svg);
        
        return { width: bounds.width, height: bounds.height };
    }
    
    buildGraph(nodes, edges) {
        this.children = new Map();
        this.parents = new Map();
        
        nodes.forEach(n => {
            this.children.set(n.id, []);
            this.parents.set(n.id, []);
        });
        
        edges.forEach(e => {
            this.children.get(e.from)?.push({ to: e.to, branch: e.branch, label: e.label });
            this.parents.get(e.to)?.push({ from: e.from, branch: e.branch });
        });
    }
    
    calculateClassPositions(nodes, edges) {
        const classNode = nodes.find(n => n.type === 'class_start');
        const fieldsNode = nodes.find(n => n.type === 'input');
        const methodNodes = nodes.filter(n => n.type === 'method');
        
        const centerX = 300;
        let y = this.padding;
        
        if (classNode) {
            this.nodePositions.set(classNode.id, { x: centerX, y });
            y += this.nodeHeight + this.verticalGap;
        }
        
        if (fieldsNode) {
            this.nodePositions.set(fieldsNode.id, { x: centerX, y });
            y += this.nodeHeight + this.verticalGap;
        }
        
        if (methodNodes.length > 0) {
            const totalWidth = (methodNodes.length - 1) * (this.nodeWidth + 30);
            let startX = centerX - totalWidth / 2;
            
            methodNodes.forEach((method, i) => {
                this.nodePositions.set(method.id, { 
                    x: startX + i * (this.nodeWidth + 30), 
                    y 
                });
            });
        }
    }
    
    calculatePositions(nodes, edges) {
        let startNode = nodes.find(n => n.type === 'start');
        if (!startNode) startNode = nodes[0];
        if (!startNode) return;
        
        const positioned = new Set();
        const centerX = 350;
        
        this.positionNode(startNode.id, centerX, this.padding, nodes, positioned, new Set());
    }
    
    positionNode(nodeId, x, y, nodes, positioned, visiting) {
        if (positioned.has(nodeId)) {
            return this.nodePositions.get(nodeId)?.y || y;
        }
        
        if (visiting.has(nodeId)) {
            return y;
        }
        visiting.add(nodeId);
        
        const node = nodes.find(n => n.id === nodeId);
        if (!node) return y;
        
        this.nodePositions.set(nodeId, { x, y });
        positioned.add(nodeId);
        
        const children = this.children.get(nodeId) || [];
        const forwardChildren = children.filter(c => c.branch !== 'loop_back');
        
        let maxY = y;
        const nodeH = this.getNodeFullHeight(node);
        
        // Условие (if)
        if (node.type === 'condition') {
            const yesChild = forwardChildren.find(c => c.branch === 'yes');
            const noChild = forwardChildren.find(c => c.branch === 'no');
            const exitChildren = forwardChildren.filter(c => c.branch !== 'yes' && c.branch !== 'no');
            
            if (yesChild && !positioned.has(yesChild.to)) {
                const yesY = this.positionNode(
                    yesChild.to, x, y + this.verticalGap + nodeH,
                    nodes, positioned, new Set(visiting)
                );
                maxY = Math.max(maxY, yesY);
            }
            
            if (noChild && !positioned.has(noChild.to)) {
                const noX = x + this.horizontalGap + this.nodeWidth / 2;
                const noY = this.positionNode(
                    noChild.to, noX, y,
                    nodes, positioned, new Set(visiting)
                );
                maxY = Math.max(maxY, noY);
            }
            
            exitChildren.forEach(child => {
                if (!positioned.has(child.to)) {
                    const exitY = this.positionNode(
                        child.to, x, maxY + this.verticalGap + this.nodeHeight,
                        nodes, positioned, new Set(visiting)
                    );
                    maxY = Math.max(maxY, exitY);
                }
            });
            
            return maxY;
        }
        
        // Цикл (loop)
        if (node.type === 'loop') {
            const bodyChild = forwardChildren.find(c => c.branch === 'loop_body');
            const exitChildren = forwardChildren.filter(c => c.branch !== 'loop_body');
            
            if (bodyChild && !positioned.has(bodyChild.to)) {
                const bodyY = this.positionNode(
                    bodyChild.to, x, y + this.verticalGap + nodeH,
                    nodes, positioned, new Set(visiting)
                );
                maxY = Math.max(maxY, bodyY);
            }
            
            exitChildren.forEach(child => {
                if (!positioned.has(child.to)) {
                    const exitY = this.positionNode(
                        child.to, x, maxY + this.verticalGap + this.nodeHeight,
                        nodes, positioned, new Set(visiting)
                    );
                    maxY = Math.max(maxY, exitY);
                }
            });
            
            return maxY;
        }
        
        // Обычный узел
        let nextY = y + this.verticalGap + nodeH;
        
        forwardChildren.forEach(child => {
            if (!positioned.has(child.to)) {
                const childY = this.positionNode(
                    child.to, x, nextY,
                    nodes, positioned, new Set(visiting)
                );
                maxY = Math.max(maxY, childY);
                nextY = maxY + this.verticalGap + this.nodeHeight;
            }
        });
        
        return Math.max(y, maxY);
    }
    
    getNodeFullHeight(node) {
        if (node.type === 'condition') return this.conditionSize * 2;
        if (node.type === 'loop') return this.hexHeight;
        if (node.type === 'end') return 30;
        return this.nodeHeight;
    }
    
    getBounds(nodes) {
        let minX = Infinity, maxX = -Infinity;
        let minY = Infinity, maxY = -Infinity;
        
        this.nodePositions.forEach(pos => {
            minX = Math.min(minX, pos.x - this.nodeWidth / 2 - this.loopLeftOffset);
            maxX = Math.max(maxX, pos.x + this.nodeWidth / 2 + this.horizontalGap);
            minY = Math.min(minY, pos.y - this.nodeHeight - 30);
            maxY = Math.max(maxY, pos.y + this.nodeHeight + 30);
        });
        
        if (!isFinite(minX)) return { width: 600, height: 400 };
        
        const offsetX = this.padding - minX;
        const offsetY = this.padding - minY;
        
        this.nodePositions.forEach(pos => {
            pos.x += offsetX;
            pos.y += offsetY;
        });
        
        return {
            width: Math.max(500, (maxX - minX) + this.padding * 2),
            height: Math.max(300, (maxY - minY) + this.padding * 2)
        };
    }
    
    addArrowMarker() {
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
    
    // === ОТРИСОВКА УЗЛОВ ===
    
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
                this.drawEndSymbol(g, pos.x, pos.y);
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
            case 'loop':
                this.drawHexagon(g, pos.x, pos.y, node.text);
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
        if (withCircle) {
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', x);
            circle.setAttribute('cy', y - this.nodeHeight / 2 - 15);
            circle.setAttribute('r', 8);
            circle.setAttribute('fill', this.colors.stroke);
            g.appendChild(circle);
        }
        
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', x - this.nodeWidth / 2);
        rect.setAttribute('y', y - this.nodeHeight / 2);
        rect.setAttribute('width', this.nodeWidth);
        rect.setAttribute('height', this.nodeHeight);
        rect.setAttribute('rx', this.nodeHeight / 2);
        rect.setAttribute('fill', this.colors.fill);
        rect.setAttribute('stroke', this.colors.stroke);
        rect.setAttribute('stroke-width', '2');
        g.appendChild(rect);
        
        g.appendChild(this.createText(x, y, text));
    }
    
    drawEndSymbol(g, x, y) {
        const size = 15;
        const outer = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        outer.setAttribute('points', `${x},${y-size} ${x+size},${y} ${x},${y+size} ${x-size},${y}`);
        outer.setAttribute('fill', 'white');
        outer.setAttribute('stroke', this.colors.stroke);
        outer.setAttribute('stroke-width', '2');
        g.appendChild(outer);
        
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
        if (dashed) rect.setAttribute('stroke-dasharray', '5,3');
        g.appendChild(rect);
        
        g.appendChild(this.createText(x, y, text));
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
        
        g.appendChild(this.createText(x, y, text));
    }
    
    drawDiamond(g, x, y, text) {
        const size = this.conditionSize;
        const points = `${x},${y-size} ${x+size},${y} ${x},${y+size} ${x-size},${y}`;
        
        const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        poly.setAttribute('points', points);
        poly.setAttribute('fill', this.colors.fill);
        poly.setAttribute('stroke', this.colors.stroke);
        poly.setAttribute('stroke-width', '2');
        g.appendChild(poly);
        
        g.appendChild(this.createText(x, y, text, size * 1.6));
    }
    
    drawHexagon(g, x, y, text) {
        const w = this.hexWidth / 2;
        const h = this.hexHeight / 2;
        const cut = 20;
        
        const points = [
            `${x - w + cut},${y - h}`,
            `${x + w - cut},${y - h}`,
            `${x + w},${y}`,
            `${x + w - cut},${y + h}`,
            `${x - w + cut},${y + h}`,
            `${x - w},${y}`
        ].join(' ');
        
        const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        poly.setAttribute('points', points);
        poly.setAttribute('fill', this.colors.fill);
        poly.setAttribute('stroke', this.colors.stroke);
        poly.setAttribute('stroke-width', '2');
        g.appendChild(poly);
        
        g.appendChild(this.createText(x, y, text, this.hexWidth - 50));
    }
    
    // === ОТРИСОВКА СВЯЗЕЙ ===
    
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
        
        if (edge.label) {
            this.drawEdgeLabel(fromPos, toPos, fromNode, toNode, edge);
        }
    }
    
    calculatePath(from, to, fromNode, toNode, edge) {
        // Получаем точки выхода и входа
        const fromBottom = this.getBottomPoint(from, fromNode);
        const fromRight = this.getRightPoint(from, fromNode);
        const fromLeft = this.getLeftPoint(from, fromNode);
        const toTop = this.getTopPoint(to, toNode);
        const toLeft = this.getLeftPoint(to, toNode);
        
        // Веер от полей класса к методам
        if (edge.branch?.startsWith('fan_')) {
            const x1 = from.x;
            const y1 = fromBottom.y;
            const x2 = to.x;
            const y2 = toTop.y;
            
            const midY = y1 + (y2 - y1) / 3;
            return `M ${x1} ${y1} L ${x1} ${midY} L ${x2} ${midY} L ${x2} ${y2}`;
        }
        
        // Обратная связь цикла - СЛЕВА
        if (edge.branch === 'loop_back') {
            const x1 = fromLeft.x;
            const y1 = fromLeft.y;
            const x2 = toLeft.x;
            const y2 = toLeft.y;
            
            const loopX = Math.min(x1, x2) - this.loopLeftOffset;
            return `M ${x1} ${y1} L ${loopX} ${y1} L ${loopX} ${y2} L ${x2} ${y2}`;
        }
        
        // Тело цикла - вниз
        if (edge.branch === 'loop_body') {
            const x1 = fromBottom.x;
            const y1 = fromBottom.y;
            const x2 = toTop.x;
            const y2 = toTop.y;
            
            // Прямая линия вниз с небольшим отступом
            if (Math.abs(x1 - x2) < 5) {
                return `M ${x1} ${y1} L ${x2} ${y2}`;
            }
            // Если не по центру - с изломом
            const midY = y1 + this.arrowGap;
            return `M ${x1} ${y1} L ${x1} ${midY} L ${x2} ${midY} L ${x2} ${y2}`;
        }
        
        // Выход из цикла - СПРАВА и потом ВНИЗ к центру следующего блока
        if (fromNode?.type === 'loop' && !edge.branch) {
            const x1 = fromRight.x;
            const y1 = fromRight.y;
            const x2 = toTop.x;
            const y2 = toTop.y;
            
            // Вправо, потом вниз, потом к блоку сверху
            const rightX = Math.max(x1 + this.arrowGap, to.x + this.nodeWidth / 2 + this.arrowGap);
            const topY = y2 - this.arrowGap;
            
            return `M ${x1} ${y1} L ${rightX} ${y1} L ${rightX} ${topY} L ${x2} ${topY} L ${x2} ${y2}`;
        }
        
        // "да" от условия - ВНИЗ
        if (edge.branch === 'yes') {
            const x1 = fromBottom.x;
            const y1 = fromBottom.y;
            const x2 = toTop.x;
            const y2 = toTop.y;
            
            if (Math.abs(x1 - x2) < 5) {
                return `M ${x1} ${y1} L ${x2} ${y2}`;
            }
            const midY = y1 + this.arrowGap;
            return `M ${x1} ${y1} L ${x1} ${midY} L ${x2} ${midY} L ${x2} ${y2}`;
        }
        
        // "нет" от условия - ВПРАВО, ОБХОД справа, потом ВНИЗ к блоку
        if (edge.branch === 'no') {
            const x1 = fromRight.x;
            const y1 = fromRight.y;
            const x2 = toTop.x;
            const y2 = toTop.y;
            
            // Если цель на том же уровне (рядом справа)
            if (Math.abs(from.y - to.y) < 10 && to.x > from.x) {
                return `M ${x1} ${y1} L ${to.x - this.nodeWidth / 2} ${y1}`;
            }
            
            // Вычисляем правую границу для обхода
            // Нужно обойти все блоки между условием и целевым блоком
            const rightOffset = this.horizontalGap;
            const bypassX = from.x + rightOffset;
            
            // Спускаемся вниз справа, затем к целевому блоку сверху
            const approachY = y2 - this.arrowGap;
            
            return `M ${x1} ${y1} L ${bypassX} ${y1} L ${bypassX} ${approachY} L ${x2} ${approachY} L ${x2} ${y2}`;
        }
        
        // Выход из ветки "нет" к следующему блоку - обходим справа
        if (edge.branch === 'from_no') {
            const x1 = fromRight.x;
            const y1 = fromRight.y;
            const x2 = toTop.x;
            const y2 = toTop.y;
            
            // Вычисляем правую границу для обхода
            const rightOffset = this.horizontalGap;
            const bypassX = Math.max(from.x + rightOffset, x2 + this.nodeWidth / 2 + this.arrowGap);
            
            // Спускаемся вниз справа, затем к целевому блоку сверху
            const approachY = y2 - this.arrowGap;
            
            return `M ${x1} ${y1} L ${bypassX} ${y1} L ${bypassX} ${approachY} L ${x2} ${approachY} L ${x2} ${y2}`;
        }
        
        // Исключение
        if (edge.branch === 'exception') {
            const x1 = from.x + this.nodeWidth / 2;
            const y1 = from.y;
            const x2 = toTop.x;
            const y2 = toTop.y;
            
            const midX = x1 + this.arrowGap;
            const topY = y2 - this.arrowGap;
            return `M ${x1} ${y1} L ${midX} ${y1} L ${midX} ${topY} L ${x2} ${topY} L ${x2} ${y2}`;
        }
        
        // Обычная связь - ВНИЗ с гарантированным вертикальным входом
        const x1 = fromBottom.x;
        const y1 = fromBottom.y;
        const x2 = toTop.x;
        const y2 = toTop.y;
        
        // Если на одной линии - просто вертикаль
        if (Math.abs(x1 - x2) < 5) {
            return `M ${x1} ${y1} L ${x2} ${y2}`;
        }
        
        // Иначе - с изломом, и обязательно входим сверху
        const midY = y1 + this.arrowGap;
        const topY = y2 - this.arrowGap;
        
        return `M ${x1} ${y1} L ${x1} ${midY} L ${x2} ${midY} L ${x2} ${y2}`;
    }
    
    // Точки выхода/входа для разных типов узлов
    getBottomPoint(pos, node) {
        if (!node) return { x: pos.x, y: pos.y + this.nodeHeight / 2 };
        
        switch (node.type) {
            case 'condition':
                return { x: pos.x, y: pos.y + this.conditionSize };
            case 'loop':
                return { x: pos.x, y: pos.y + this.hexHeight / 2 };
            case 'end':
                return { x: pos.x, y: pos.y + 15 };
            default:
                return { x: pos.x, y: pos.y + this.nodeHeight / 2 };
        }
    }
    
    getTopPoint(pos, node) {
        if (!node) return { x: pos.x, y: pos.y - this.nodeHeight / 2 };
        
        switch (node.type) {
            case 'condition':
                return { x: pos.x, y: pos.y - this.conditionSize };
            case 'loop':
                return { x: pos.x, y: pos.y - this.hexHeight / 2 };
            case 'end':
                return { x: pos.x, y: pos.y - 15 };
            default:
                return { x: pos.x, y: pos.y - this.nodeHeight / 2 };
        }
    }
    
    getRightPoint(pos, node) {
        if (!node) return { x: pos.x + this.nodeWidth / 2, y: pos.y };
        
        switch (node.type) {
            case 'condition':
                return { x: pos.x + this.conditionSize, y: pos.y };
            case 'loop':
                return { x: pos.x + this.hexWidth / 2, y: pos.y };
            default:
                return { x: pos.x + this.nodeWidth / 2, y: pos.y };
        }
    }
    
    getLeftPoint(pos, node) {
        if (!node) return { x: pos.x - this.nodeWidth / 2, y: pos.y };
        
        switch (node.type) {
            case 'condition':
                return { x: pos.x - this.conditionSize, y: pos.y };
            case 'loop':
                return { x: pos.x - this.hexWidth / 2, y: pos.y };
            default:
                return { x: pos.x - this.nodeWidth / 2, y: pos.y };
        }
    }
    
    drawEdgeLabel(from, to, fromNode, toNode, edge) {
        let x, y;
        
        if (edge.branch === 'yes') {
            x = from.x - 20;
            y = from.y + this.conditionSize + 18;
        } else if (edge.branch === 'no') {
            x = from.x + this.conditionSize + 8;
            y = from.y - 8;
        } else if (edge.branch === 'exception') {
            x = from.x + this.nodeWidth / 2 + 8;
            y = from.y - 8;
        } else {
            return;
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
    
    createText(x, y, text, maxWidth = 160) {
        const textEl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        textEl.setAttribute('x', x);
        textEl.setAttribute('y', y);
        textEl.setAttribute('text-anchor', 'middle');
        textEl.setAttribute('dominant-baseline', 'middle');
        textEl.setAttribute('font-family', 'Arial, sans-serif');
        textEl.setAttribute('font-size', '11');
        textEl.setAttribute('fill', this.colors.text);
        
        if (!text) return textEl;
        
        const words = text.split(' ');
        const lines = [];
        let currentLine = '';
        
        words.forEach(word => {
            const testLine = currentLine ? currentLine + ' ' + word : word;
            if (testLine.length * 6.5 > maxWidth && currentLine) {
                lines.push(currentLine);
                currentLine = word;
            } else {
                currentLine = testLine;
            }
        });
        if (currentLine) lines.push(currentLine);
        
        if (lines.length > 3) {
            lines.length = 3;
            lines[2] = lines[2].substring(0, Math.max(0, lines[2].length - 3)) + '...';
        }
        
        if (lines.length === 1) {
            const displayText = text.length > 28 ? text.substring(0, 25) + '...' : text;
            textEl.textContent = displayText;
        } else {
            const lineHeight = 13;
            const startY = y - ((lines.length - 1) * lineHeight) / 2;
            
            lines.forEach((line, i) => {
                const tspan = document.createElementNS('http://www.w3.org/2000/svg', 'tspan');
                tspan.setAttribute('x', x);
                tspan.setAttribute('y', startY + i * lineHeight);
                const displayLine = line.length > 24 ? line.substring(0, 21) + '...' : line;
                tspan.textContent = displayLine;
                textEl.appendChild(tspan);
            });
        }
        
        return textEl;
    }
}

window.FlowchartRenderer = FlowchartRenderer;
