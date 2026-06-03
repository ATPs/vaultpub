/**
 * Interactive graph visualization.
 * Canvas-based force-directed layout rendering graph.json data.
 */

interface GraphNode {
  id: string;
  label: string;
  group: string;
  url: string | null;
}

interface GraphEdge {
  from: string;
  to: string;
  kind: string;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

let graphData: GraphData | null = null;

async function loadGraphData(): Promise<GraphData | null> {
  try {
    const resp = await fetch("/graph.json");
    if (!resp.ok) return null;
    return await resp.json();
  } catch {
    try {
      const resp = await fetch("/api/graph");
      if (!resp.ok) return null;
      return await resp.json();
    } catch {
      return null;
    }
  }
}

interface SimNode {
  id: string;
  label: string;
  group: string;
  url: string | null;
  x: number;
  y: number;
  vx: number;
  vy: number;
}

function createGraphCanvas(container: HTMLElement): HTMLCanvasElement {
  const canvas = document.createElement("canvas");
  canvas.width = container.clientWidth || 600;
  canvas.height = container.clientHeight || 400;
  canvas.style.width = "100%";
  canvas.style.height = "100%";
  container.appendChild(canvas);
  return canvas;
}

function simulate(nodes: SimNode[], edges: GraphEdge[], iterations: number = 50): void {
  const area = nodes.length * 5000;
  const k = Math.sqrt(area / nodes.length);
  const temp = 10;

  // Random initial positions
  for (const n of nodes) {
    n.x = Math.random() * 800;
    n.y = Math.random() * 500;
  }

  for (let iter = 0; iter < iterations; iter++) {
    const t = temp * (1 - iter / iterations);

    // Repulsion
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
        const force = (k * k) / dist;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        nodes[i].x += fx * t * 0.01;
        nodes[i].y += fy * t * 0.01;
        nodes[j].x -= fx * t * 0.01;
        nodes[j].y -= fy * t * 0.01;
      }
    }

    // Attraction
    const nodeMap = new Map(nodes.map((n) => [n.id, n]));
    for (const edge of edges) {
      const source = nodeMap.get(edge.from);
      const target = nodeMap.get(edge.to);
      if (!source || !target) continue;
      const dx = target.x - source.x;
      const dy = target.y - source.y;
      const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
      const force = (dist * dist) / k;
      const fx = (dx / dist) * force * 0.01;
      const fy = (dy / dist) * force * 0.01;
      source.x += fx;
      source.y += fy;
      target.x -= fx;
      target.y -= fy;
    }

    // Center gravity
    for (const n of nodes) {
      n.x += (400 - n.x) * 0.001;
      n.y += (250 - n.y) * 0.001;
    }
  }
}

function render(canvas: HTMLCanvasElement, nodes: SimNode[], edges: GraphEdge[]): void {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const dpr = window.devicePixelRatio || 1;
  canvas.width = canvas.clientWidth * dpr;
  canvas.height = canvas.clientHeight * dpr;
  ctx.scale(dpr, dpr);

  const w = canvas.clientWidth;
  const h = canvas.clientHeight;

  ctx.clearRect(0, 0, w, h);

  // Edges
  const nodeMap = new Map(nodes.map((n) => [n.id, n]));
  ctx.strokeStyle = "var(--graph-edge-color, #999)";
  ctx.lineWidth = 0.5;
  for (const edge of edges) {
    const source = nodeMap.get(edge.from);
    const target = nodeMap.get(edge.to);
    if (!source || !target) continue;
    ctx.beginPath();
    ctx.moveTo(source.x, source.y);
    ctx.lineTo(target.x, target.y);
    ctx.stroke();
  }

  // Nodes
  const colors: Record<string, string> = {
    note: "var(--graph-note-color, #4a9eff)",
    tag: "var(--graph-tag-color, #e67e22)",
    attachment: "var(--graph-attachment-color, #2ecc71)",
  };

  for (const n of nodes) {
    const r = n.group === "tag" ? 3 : 5;
    ctx.fillStyle = colors[n.group] || "#999";
    ctx.beginPath();
    ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
    ctx.fill();

    if (n.group === "note") {
      ctx.fillStyle = "var(--graph-label-color, #333)";
      ctx.font = "9px sans-serif";
      ctx.fillText(n.label.slice(0, 15), n.x + 6, n.y + 4);
    }
  }
}

export async function initGraph(): Promise<void> {
  const container = document.getElementById("graph-container");
  if (!container) return;

  graphData = await loadGraphData();
  if (!graphData || graphData.nodes.length === 0) {
    container.innerHTML = '<p class="graph-empty">No graph data available.</p>';
    return;
  }

  const canvas = createGraphCanvas(container);

  const simNodes: SimNode[] = graphData.nodes.map((n) => ({
    id: n.id,
    label: n.label,
    group: n.group,
    url: n.url,
    x: 0,
    y: 0,
    vx: 0,
    vy: 0,
  }));

  simulate(simNodes, graphData.edges, 80);
  render(canvas, simNodes, graphData.edges);

  // Click to navigate
  canvas.addEventListener("click", (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const nodeMap = new Map(simNodes.map((n) => [n.id, n]));

    for (const n of simNodes) {
      const dx = n.x - mx;
      const dy = n.y - my;
      if (Math.sqrt(dx * dx + dy * dy) < 10 && n.url) {
        window.location.href = n.url;
        return;
      }
    }
  });

  // Resize handler
  const observer = new ResizeObserver(() => {
    render(canvas, simNodes, graphData?.edges || []);
  });
  observer.observe(container);
}
