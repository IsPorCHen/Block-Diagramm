class FlowchartRenderer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.blockWidth = 180;
        this.blockHeight = 60;
        this.verticalGap = 40;
        this.horizontalGap = 60;
        this.currentY = 50;
        this.svgElements = [];
    }
    
    render(blocks) {
        this.container.innerHTML = '';
        this.currentY = 50;
        this.svgElements = [];
        
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '100%');
        svg.style.display = 'block';
        svg.style.margin = '0 auto';

        let prevBlock = null;
        blocks.forEach((block, index) => {
            const element = this.drawBlock(svg, block, prevBlock);
            prevBlock = { ...block, element, y: this.currentY };
            this.currentY += this.blockHeight + this.verticalGap;
        });
        
        const totalHeight = this.currentY + 50;
        svg.setAttribute('height', totalHeight);
        svg.setAttribute('viewBox', `0 0 800 ${totalHeight}`);
        
        this.container.appendChild(svg);
    }
    
    drawBlock(svg, block, prevBlock) {
        const centerX = 400;
        
        // лииня от предыдущей операции
        if (prevBlock) {
            this.drawLine(svg, centerX, prevBlock.y + this.blockHeight / 2, centerX, this.currentY);
        }
        
        let element;
        
        switch (block.type) {
            case 'start':
            case 'end':
                element = this.drawTerminal(svg, centerX, this.currentY, block.text);
                break;
            case 'operation':
                element = this.drawProcess(svg, centerX, this.currentY, block.text);
                break;
            case 'input':
            case 'output':
                element = this.drawIO(svg, centerX, this.currentY, block.text);
                break;
            case 'condition':
                element = this.drawDecision(svg, centerX, this.currentY, block.text);
                break;
            case 'loop':
                element = this.drawLoop(svg, centerX, this.currentY, block.text);
                break;
            default:
                element = this.drawProcess(svg, centerX, this.currentY, block.text);
        }
        
        return element;
    }
    
    drawTerminal(svg, x, y, text) {
        // начало и конец
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        
        const ellipse = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
        ellipse.setAttribute('cx', x);
        ellipse.setAttribute('cy', y);
        ellipse.setAttribute('rx', this.blockWidth / 2);
        ellipse.setAttribute('ry', this.blockHeight / 2);
        ellipse.setAttribute('fill', '#dbeafe');
        ellipse.setAttribute('stroke', '#2563eb');
        ellipse.setAttribute('stroke-width', '2');
        
        const textEl = this.createText(x, y, text);
        
        group.appendChild(ellipse);
        group.appendChild(textEl);
        svg.appendChild(group);
        
        return group;
    }
    
    drawProcess(svg, x, y, text) {
        // действие
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', x - this.blockWidth / 2);
        rect.setAttribute('y', y - this.blockHeight / 2);
        rect.setAttribute('width', this.blockWidth);
        rect.setAttribute('height', this.blockHeight);
        rect.setAttribute('fill', '#dbeafe');
        rect.setAttribute('stroke', '#2563eb');
        rect.setAttribute('stroke-width', '2');
        rect.setAttribute('rx', '5');
        
        const textEl = this.createText(x, y, text);
        
        group.appendChild(rect);
        group.appendChild(textEl);
        svg.appendChild(group);
        
        return group;
    }
    
    drawIO(svg, x, y, text) {
        // ввод/вывод
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        
        const offset = 20;
        const points = [
            [x - this.blockWidth / 2 + offset, y - this.blockHeight / 2],
            [x + this.blockWidth / 2 + offset, y - this.blockHeight / 2],
            [x + this.blockWidth / 2 - offset, y + this.blockHeight / 2],
            [x - this.blockWidth / 2 - offset, y + this.blockHeight / 2]
        ];
        
        const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon.setAttribute('points', points.map(p => p.join(',')).join(' '));
        polygon.setAttribute('fill', '#dbeafe');
        polygon.setAttribute('stroke', '#2563eb');
        polygon.setAttribute('stroke-width', '2');
        
        const textEl = this.createText(x, y, text);
        
        group.appendChild(polygon);
        group.appendChild(textEl);
        svg.appendChild(group);
        
        return group;
    }
    
    drawDecision(svg, x, y, text) {
        // условие
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        
        const size = 80;
        const points = [
            [x, y - size / 2],
            [x + size / 2, y],
            [x, y + size / 2],
            [x - size / 2, y]
        ];
        
        const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon.setAttribute('points', points.map(p => p.join(',')).join(' '));
        polygon.setAttribute('fill', '#dbeafe');
        polygon.setAttribute('stroke', '#2563eb');
        polygon.setAttribute('stroke-width', '2');
        
        const textEl = this.createText(x, y, text, 70);
        
        group.appendChild(polygon);
        group.appendChild(textEl);
        svg.appendChild(group);
        
        return group;
    }
    
    drawLoop(svg, x, y, text) {
        // циклы
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        
        const offset = 25;
        const points = [
            [x - this.blockWidth / 2 + offset, y - this.blockHeight / 2],
            [x + this.blockWidth / 2 - offset, y - this.blockHeight / 2],
            [x + this.blockWidth / 2, y],
            [x + this.blockWidth / 2 - offset, y + this.blockHeight / 2],
            [x - this.blockWidth / 2 + offset, y + this.blockHeight / 2],
            [x - this.blockWidth / 2, y]
        ];
        
        const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon.setAttribute('points', points.map(p => p.join(',')).join(' '));
        polygon.setAttribute('fill', '#dbeafe');
        polygon.setAttribute('stroke', '#2563eb');
        polygon.setAttribute('stroke-width', '2');
        
        const textEl = this.createText(x, y, text);
        
        group.appendChild(polygon);
        group.appendChild(textEl);
        svg.appendChild(group);
        
        return group;
    }
    
    drawLine(svg, x1, y1, x2, y2) {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', x1);
        line.setAttribute('y1', y1);
        line.setAttribute('x2', x2);
        line.setAttribute('y2', y2);
        line.setAttribute('stroke', '#2563eb');
        line.setAttribute('stroke-width', '2');
        line.setAttribute('marker-end', 'url(#arrowhead)');
        
        svg.appendChild(line);

        if (!svg.querySelector('#arrowhead')) {
            const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
            const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
            marker.setAttribute('id', 'arrowhead');
            marker.setAttribute('markerWidth', '10');
            marker.setAttribute('markerHeight', '10');
            marker.setAttribute('refX', '9');
            marker.setAttribute('refY', '3');
            marker.setAttribute('orient', 'auto');
            
            const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
            polygon.setAttribute('points', '0 0, 10 3, 0 6');
            polygon.setAttribute('fill', '#2563eb');
            
            marker.appendChild(polygon);
            defs.appendChild(marker);
            svg.insertBefore(defs, svg.firstChild);
        }
    }
    
    createText(x, y, text, maxWidth = 160) {
        const textEl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        textEl.setAttribute('x', x);
        textEl.setAttribute('y', y);
        textEl.setAttribute('text-anchor', 'middle');
        textEl.setAttribute('dominant-baseline', 'middle');
        textEl.setAttribute('font-family', '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif');
        textEl.setAttribute('font-size', '12');
        textEl.setAttribute('fill', '#1e293b');
        
        const words = text.split(' ');
        const lines = [];
        let currentLine = '';
        
        words.forEach(word => {
            const testLine = currentLine ? currentLine + ' ' + word : word;
            if (testLine.length * 7 > maxWidth) {
                if (currentLine) lines.push(currentLine);
                currentLine = word;
            } else {
                currentLine = testLine;
            }
        });
        if (currentLine) lines.push(currentLine);
        
        if (lines.length === 1) {
            textEl.textContent = text;
        } else {
            const lineHeight = 16;
            const startY = y - ((lines.length - 1) * lineHeight) / 2;
            
            lines.forEach((line, index) => {
                const tspan = document.createElementNS('http://www.w3.org/2000/svg', 'tspan');
                tspan.setAttribute('x', x);
                tspan.setAttribute('y', startY + index * lineHeight);
                tspan.textContent = line;
                textEl.appendChild(tspan);
            });
        }
        
        return textEl;
    }
}

window.FlowchartRenderer = FlowchartRenderer;