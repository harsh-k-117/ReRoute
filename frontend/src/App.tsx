import { useMemo, useState } from 'react';
import {
  AlertTriangle,
  ArrowRight,
  Check,
  ChevronDown,
  Clock3,
  Download,
  ExternalLink,
  Fuel,
  MapPin,
  Menu,
  MoreHorizontal,
  Navigation,
  Plus,
  RefreshCw,
  Route,
  Search,
  SlidersHorizontal,
  Truck,
  X,
} from 'lucide-react';

type Stop = {
  location: string;
  arrival: string;
  start: string;
  end: string;
  load: number;
  kind?: 'wait';
};

type VehiclePlan = {
  id: string;
  driver: string;
  color: string;
  capacity: number;
  stops: Stop[];
};

const baseVehicles: VehiclePlan[] = [
  {
    id: 'V1', driver: 'Van 1', color: '#668bff', capacity: 5,
    stops: [
      { location: 'Alder St', arrival: '08:10', start: '08:20', end: '08:25', load: 2, kind: 'wait' },
      { location: 'Birch Ave', arrival: '08:30', start: '08:30', end: '08:35', load: 0 },
    ],
  },
  {
    id: 'V2', driver: 'Van 2', color: '#39b995', capacity: 6,
    stops: [
      { location: 'Cedar Way', arrival: '08:20', start: '08:20', end: '08:25', load: 4 },
      { location: 'Elm Market', arrival: '08:30', start: '08:30', end: '08:35', load: 2 },
      { location: 'Cedar Way', arrival: '08:40', start: '08:40', end: '08:45', load: 0 },
    ],
  },
  {
    id: 'V3', driver: 'Van 3', color: '#e4a24a', capacity: 6,
    stops: [
      { location: 'Fir Square', arrival: '08:30', start: '08:30', end: '08:35', load: 4 },
      { location: 'Fir Square', arrival: '08:35', start: '08:35', end: '08:40', load: 2 },
      { location: 'Elm Market', arrival: '08:45', start: '08:50', end: '08:55', load: 0, kind: 'wait' },
    ],
  },
];

const deliveries = [
  { id: 'D1', customer: 'Alder Street Books', location: 'Alder', window: '08:20 – 09:00', vehicle: 'V1', load: '3 crates', status: 'On route', color: 'blue' },
  { id: 'D2', customer: 'Birch & Co.', location: 'Birch', window: '08:30 – 09:10', vehicle: 'V1', load: '2 crates', status: 'On route', color: 'blue' },
  { id: 'D3', customer: 'Cedar Clinic', location: 'Cedar', window: '08:20 – 09:10', vehicle: 'V2', load: '2 crates', status: 'On route', color: 'green' },
  { id: 'D4', customer: 'Elm Corner Shop', location: 'Elm', window: '08:30 – 09:20', vehicle: 'V2', load: '2 crates', status: 'On route', color: 'green' },
  { id: 'D5', customer: 'Cedar Grocers', location: 'Cedar', window: '08:20 – 09:20', vehicle: 'V2', load: '2 crates', status: 'On route', color: 'green' },
  { id: 'D6', customer: 'Fir Pharmacy', location: 'Fir', window: '08:30 – 09:30', vehicle: 'V3', load: '2 crates', status: 'On route', color: 'amber' },
  { id: 'D7', customer: 'Fir Hardware', location: 'Fir', window: '08:30 – 09:40', vehicle: 'V3', load: '2 crates', status: 'On route', color: 'amber' },
  { id: 'D8', customer: 'Elm Florist', location: 'Elm', window: '08:50 – 09:50', vehicle: 'V3', load: '2 crates', status: 'On route', color: 'amber' },
];

const mapPoints = [
  { id: 'Depot', x: 47, y: 51, type: 'depot' },
  { id: 'Alder St', x: 24, y: 23 },
  { id: 'Birch Ave', x: 15, y: 69 },
  { id: 'Cedar Way', x: 69, y: 22 },
  { id: 'Elm Market', x: 82, y: 67 },
  { id: 'Fir Square', x: 50, y: 84 },
];

const routes = [
  { color: '#668bff', points: '47,51 35,38 24,23 19,46 15,69' },
  { color: '#39b995', points: '47,51 58,37 69,22 77,44 82,67 69,22' },
  { color: '#e4a24a', points: '47,51 49,67 50,84 56,76 82,67' },
];

function App() {
  const [selectedRange, setSelectedRange] = useState('Today, Oct 11');
  const [eventType, setEventType] = useState<'closure' | 'failure' | 'urgent'>('closure');
  const [previewState, setPreviewState] = useState<'idle' | 'preview' | 'confirmed'>('idle');
  const [menuOpen, setMenuOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [activeNav, setActiveNav] = useState('Dispatch board');

  const visibleDeliveries = useMemo(() => deliveries.filter((delivery) =>
    `${delivery.id} ${delivery.customer} ${delivery.location} ${delivery.vehicle}`.toLowerCase().includes(query.toLowerCase()),
  ), [query]);

  const previewDisruption = () => setPreviewState('preview');
  const confirmDisruption = () => setPreviewState('confirmed');

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-row">
          <div className="brand-mark"><Route size={19} strokeWidth={2.4} /></div>
          <span>reroute<span className="brand-dot">.</span></span>
          <button className="icon-button sidebar-menu" aria-label="Collapse navigation"><Menu size={18} /></button>
        </div>
        <div className="workspace-switch">
          <div className="workspace-avatar">N</div>
          <div className="workspace-copy"><b>Northstar Supply</b><span>Dispatch workspace</span></div>
          <ChevronDown size={15} className="muted-icon" />
        </div>
        <div className="side-label">WORKSPACE</div>
        <nav className="main-nav" aria-label="Main navigation">
          {[
            { name: 'Dispatch board', icon: Navigation },
            { name: 'Deliveries', icon: MapPin, count: '8' },
            { name: 'Fleet', icon: Truck },
          ].map(({ name, icon: Icon, count }) => (
            <button key={name} className={`nav-item ${activeNav === name ? 'active' : ''}`} onClick={() => setActiveNav(name)}>
              <Icon size={17} /><span>{name}</span>{count && <span className="nav-count">{count}</span>}
            </button>
          ))}
        </nav>
        <div className="side-label scenarios-label">SCENARIOS</div>
        <button className="scenario-link active-scenario"><span className="scenario-dot" />Morning run <span className="scenario-live">LIVE</span></button>
        <button className="scenario-link"><span className="scenario-dot scenario-dot-gray" />Micro fixture</button>
        <button className="scenario-add"><Plus size={15} /> Create scenario</button>
        <div className="sidebar-bottom">
          <div className="status-card"><div className="status-heading"><span className="green-pulse" /> Engine status</div><div className="status-sub">Demo mode <span>Local data</span></div></div>
          <div className="profile-row"><div className="profile-avatar">HK</div><div className="profile-copy"><b>Harsh Kumar</b><span>Dispatcher</span></div><MoreHorizontal size={18} className="muted-icon" /></div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumbs"><span>Operations</span><span className="crumb-slash">/</span><b>{activeNav}</b></div>
          <div className="topbar-actions">
            <span className="demo-pill"><span /> DEMO DATA</span>
            <button className="icon-button notification-button" aria-label="Notifications"><span className="notification-dot" /> <AlertTriangle size={17} /></button>
            <div className="top-avatar">HK</div>
          </div>
        </header>

        <div className="page-wrap">
          <section className="page-heading">
            <div>
              <div className="eyebrow">SUNDAY, OCTOBER 11, 2026 <span className="eyebrow-dot">·</span> MORNING SHIFT</div>
              <h1>Dispatch board</h1>
              <p className="heading-subtitle">Your fleet at a glance. Plans change — stay one step ahead.</p>
            </div>
            <div className="heading-actions">
              <button className="button button-quiet" onClick={() => setPreviewState('idle')}><RefreshCw size={15} /> Reset view</button>
              <div className="dropdown-wrap">
                <button className="button button-outline" onClick={() => setMenuOpen(!menuOpen)}><Download size={15} /> Export <ChevronDown size={14} /></button>
                {menuOpen && <div className="dropdown-menu"><button onClick={() => setMenuOpen(false)}>Export plan as CSV</button><button onClick={() => setMenuOpen(false)}>Download route summary</button></div>}
              </div>
              <button className="button button-primary" onClick={() => { setEventType('closure'); setPreviewState('idle'); document.getElementById('disruption-panel')?.scrollIntoView({ behavior: 'smooth' }); }}><Plus size={16} /> Add disruption</button>
            </div>
          </section>

          <section className="kpi-grid" aria-label="Plan summary">
            <KpiCard label="Deliveries planned" value="8" detail="All assigned" icon={<MapPin size={16} />} trend="All clear" trendKind="positive" />
            <KpiCard label="Vehicles on route" value="3" detail="of 3 available" icon={<Truck size={17} />} trend="100% fleet" trendKind="neutral" />
            <KpiCard label="Planned travel time" value="80" unit="min" detail="15 min total waiting" icon={<Route size={16} />} trend="On schedule" trendKind="positive" />
            <KpiCard label="Window risk" value="0" detail="Stops at risk" icon={<Clock3 size={16} />} trend="On schedule" trendKind="positive" />
          </section>

          <section className="panel map-panel">
            <div className="panel-header map-panel-header">
              <div><div className="panel-title">Fleet overview <span className="live-badge"><span /> EXAMPLE PLAN</span></div><div className="panel-subtitle">Schematic view · Not to scale</div></div>
              <div className="map-header-actions"><button className="select-button" onClick={() => setSelectedRange(selectedRange === 'Today, Oct 11' ? 'Tomorrow, Oct 12' : 'Today, Oct 11')}>{selectedRange}<ChevronDown size={14} /></button><button className="square-button" aria-label="Map settings"><SlidersHorizontal size={16} /></button><button className="square-button" aria-label="Open map details"><ExternalLink size={15} /></button></div>
            </div>
            <div className="map-body">
              <div className="schematic-map" role="img" aria-label="Schematic route map showing three delivery vehicle routes from the depot">
                <div className="map-grid" />
                <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="route-svg" aria-hidden="true">
                  <path d="M5 17 L29 17 L29 34 L43 34 L43 52 L58 52 L58 72 L96 72" className="road road-main" />
                  <path d="M12 83 L27 83 L27 66 L43 66 L43 52 L67 52 L67 30 L91 30" className="road" />
                  <path d="M8 43 L26 43 L26 34 L43 34 M58 52 L76 52 L76 72 M43 66 L57 66 L57 91" className="road" />
                  {routes.map((route) => <polyline key={route.color} points={route.points} fill="none" stroke={route.color} strokeWidth="1.25" strokeLinecap="round" strokeLinejoin="round" opacity=".93" />)}
                  {mapPoints.map((point) => <g key={point.id} className="map-point" transform={`translate(${point.x},${point.y})`}>
                    {point.type === 'depot' ? <><circle r="4.2" className="depot-ring" /><circle r="2.5" className="depot-core" /><text x="0" y="8" textAnchor="middle" className="map-label depot-label">DEPOT</text></> : <><circle r="2.7" className="stop-halo" /><circle r="1.65" className="stop-core" /><text x="0" y={point.y < 30 ? -5 : 7} textAnchor="middle" className="map-label">{point.id}</text></>}
                  </g>)}
                  <g className="truck-marker" transform="translate(35,38)"><circle r="3.8" /><text y="1.3" textAnchor="middle">1</text></g>
                  <g className="truck-marker green-marker" transform="translate(77,44)"><circle r="3.8" /><text y="1.3" textAnchor="middle">2</text></g>
                  <g className="truck-marker amber-marker" transform="translate(49,68)"><circle r="3.8" /><text y="1.3" textAnchor="middle">3</text></g>
                </svg>
                <div className="map-attribution">Local schematic · No live map data</div>
              </div>
              <div className="route-legend">
                <div className="legend-heading">ACTIVE ROUTES <span>3</span></div>
                {baseVehicles.map((vehicle) => <div className="legend-route" key={vehicle.id}><span className="route-swatch" style={{ backgroundColor: vehicle.color }} /><div className="legend-route-copy"><b>{vehicle.id} <span>{vehicle.driver}</span></b><small>{vehicle.stops.length} stops <i>·</i> {vehicle.capacity} crate capacity</small></div><button className="legend-more" aria-label={`More options for ${vehicle.id}`}><MoreHorizontal size={17} /></button></div>)}
                <div className="legend-divider" />
                <div className="legend-meta"><span><span className="legend-symbol depot-symbol" /> Depot</span><span><span className="legend-symbol stop-symbol" /> Delivery stop</span></div>
                <div className="map-tip"><Fuel size={14} /><span>Vehicle loads stay within capacity across the example routes.</span></div>
              </div>
            </div>
            <div className="map-footer"><span><span className="fresh-dot" /> Example plan · 08:00 start</span><span>Micro fixture <button className="text-link">View scenario details <ArrowRight size={13} /></button></span></div>
          </section>

          <section className="panel disruption-panel" id="disruption-panel">
            <div className="panel-header disruption-heading">
              <div className="disruption-title-wrap"><div className="disruption-icon"><AlertTriangle size={17} /></div><div><div className="panel-title">Disruption simulator</div><div className="panel-subtitle">Preview a change before it reaches your plan.</div></div></div>
              <span className="preview-only-tag">LOCAL PREVIEW ONLY</span>
            </div>
            {previewState === 'idle' ? <div className="disruption-content">
              <div className="event-tabs" role="tablist" aria-label="Disruption type">
                <button className={eventType === 'closure' ? 'selected' : ''} onClick={() => setEventType('closure')}><Route size={15} /> Road closure</button>
                <button className={eventType === 'failure' ? 'selected' : ''} onClick={() => setEventType('failure')}><Truck size={15} /> Vehicle failure</button>
                <button className={eventType === 'urgent' ? 'selected' : ''} onClick={() => setEventType('urgent')}><Plus size={15} /> Urgent delivery</button>
              </div>
              <div className="event-form">
                {eventType === 'closure' && <><FormField label="FROM LOCATION"><select defaultValue="Cedar Way"><option>Cedar Way</option><option>Alder St</option><option>Birch Ave</option><option>Elm Market</option><option>Fir Square</option></select></FormField><FormField label="TO LOCATION"><select defaultValue="Elm Market"><option>Elm Market</option><option>Alder St</option><option>Birch Ave</option><option>Cedar Way</option><option>Fir Square</option></select></FormField><FormField label="DELAY"><select defaultValue="+15 min"><option>+10 min</option><option>+15 min</option><option>+30 min</option><option>+45 min</option></select></FormField><FormField label="ACTIVE PERIOD"><select defaultValue="08:00 – 10:00"><option>08:00 – 10:00</option><option>08:30 – 09:30</option><option>09:00 – 11:00</option></select></FormField></>}
                {eventType === 'failure' && <><FormField label="VEHICLE"><select defaultValue="V2"><option>V1</option><option>V2</option><option>V3</option></select></FormField><FormField label="FAILURE TIME"><select defaultValue="08:25"><option>08:15</option><option>08:25</option><option>08:35</option><option>08:45</option></select></FormField><FormField label="LOCATION"><select defaultValue="Cedar Way"><option>Alder St</option><option>Birch Ave</option><option>Cedar Way</option><option>Elm Market</option><option>Fir Square</option></select></FormField><div className="field-note"><AlertTriangle size={14} /> Completed stops remain fixed in the revised plan.</div></>}
                {eventType === 'urgent' && <><FormField label="DELIVERY LOCATION"><select defaultValue="Birch Ave"><option>Alder St</option><option>Birch Ave</option><option>Cedar Way</option><option>Elm Market</option><option>Fir Square</option></select></FormField><FormField label="LOAD"><select defaultValue="1 crate"><option>1 crate</option><option>2 crates</option><option>3 crates</option></select></FormField><FormField label="TIME WINDOW"><select defaultValue="09:00 – 10:00"><option>08:30 – 09:30</option><option>09:00 – 10:00</option><option>10:00 – 11:00</option></select></FormField><FormField label="PRIORITY"><select defaultValue="Urgent"><option>Urgent</option><option>High</option></select></FormField></>}
              </div>
              <div className="disruption-actions"><span className="form-hint"><Check size={14} /> Changes require dispatcher confirmation</span><button className="button button-dark" onClick={previewDisruption}>Preview impact <ArrowRight size={15} /></button></div>
            </div> : <div className="preview-result">
              <div className={`preview-status ${previewState === 'confirmed' ? 'confirmed' : ''}`}><span>{previewState === 'confirmed' ? <Check size={15} /> : <AlertTriangle size={15} />}</span><div><b>{previewState === 'confirmed' ? 'Demo change confirmed' : 'Sample impact ready to review'}</b><small>{previewState === 'confirmed' ? 'This is a local visualization only; no dispatch system was updated.' : `Static ${eventType === 'closure' ? 'road closure' : eventType === 'failure' ? 'vehicle failure' : 'urgent delivery'} example — not calculated by the optimization engine.`}</small></div></div>
              <div className="impact-summary"><div><span>DELIVERIES</span><b>7 kept <i>·</i> 1 moved</b></div><div><span>WINDOWS AT RISK</span><b className="risk-value">1 <small>+5 min late</small></b></div><div><span>VEHICLES AFFECTED</span><b>V-02 <small>re-sequenced</small></b></div><div><span>CAPACITY</span><b className="capacity-good"><Check size={14} /> Within limits</b></div></div>
              <div className="preview-footer"><span><span className="diff-dot moved-dot" /> Sample diff: D5 moved from V2 to V3 <span className="reason-text">· Example only; route changes are not computed yet.</span></span><div>{previewState === 'preview' ? <><button className="button button-quiet" onClick={() => setPreviewState('idle')}>Discard</button><button className="button button-primary" onClick={confirmDisruption}>Confirm change <Check size={15} /></button></> : <button className="button button-outline" onClick={() => setPreviewState('idle')}>New preview <RefreshCw size={14} /></button>}</div></div>
              </div>}
          </section>

          <section className="panel timeline-panel">
            <div className="panel-header timeline-header"><div><div className="panel-title">Route timeline <span className="stop-count">8 stops</span></div><div className="panel-subtitle">Arrival, waiting and service time by vehicle.</div></div><button className="select-button compact-select">Today <ChevronDown size={14} /></button></div>
            <div className="timeline-content">
              <div className="time-axis"><span className="axis-spacer" />{['08:00', '08:30', '09:00', '09:30', '10:00', '10:30'].map((t) => <span key={t}>{t}</span>)}</div>
              {baseVehicles.map((vehicle) => <div className="timeline-row" key={vehicle.id}>
                <div className="timeline-vehicle"><span className="vehicle-color" style={{ backgroundColor: vehicle.color }} /><div><b>{vehicle.id}</b><small>{vehicle.driver}</small></div></div>
                <div className="timeline-track"><div className="now-line"><span>NOW</span></div>
                  {vehicle.stops.map((stop, index) => <div key={`${stop.location}-${index}`} className={`stop-block ${stop.kind === 'wait' ? 'has-wait' : ''}`} style={{ left: getTimelineLeft(stop.start), width: stop.kind === 'wait' ? '8.5%' : '5.4%', borderColor: vehicle.color, backgroundColor: `${vehicle.color}1c` }} title={`${stop.location}: arrival ${stop.arrival}, service ${stop.start}–${stop.end}`}><span className="stop-block-dot" style={{ backgroundColor: vehicle.color }} /><span>{stop.location}</span><small>{stop.kind === 'wait' ? `Wait · ${stop.arrival}` : stop.start}</small></div>)}
                </div>
              </div>)}
              <div className="timeline-legend"><span><i className="legend-service" /> Service stop</span><span><i className="legend-wait" /> Waiting for window</span><span className="arrival-note"><Clock3 size={13} /> Labels show service start; hover for arrival time</span></div>
            </div>
          </section>

          <section className="panel deliveries-panel">
            <div className="panel-header deliveries-header"><div><div className="panel-title">Delivery plan <span className="stop-count">8 total</span></div><div className="panel-subtitle">Every delivery accounted for in the current plan.</div></div><div className="table-actions"><label className="search-box"><Search size={14} /><input placeholder="Search deliveries" value={query} onChange={(event) => setQuery(event.target.value)} /></label><button className="square-button" aria-label="Filter deliveries"><SlidersHorizontal size={16} /></button></div></div>
            <div className="table-scroll"><table><thead><tr><th>DELIVERY</th><th>LOCATION</th><th>TIME WINDOW</th><th>VEHICLE</th><th>LOAD</th><th>STATUS</th><th /></tr></thead><tbody>{visibleDeliveries.map((delivery) => <tr key={delivery.id}><td><div className="delivery-name"><span>{delivery.id}</span><b>{delivery.customer}</b></div></td><td><span className="location-cell"><MapPin size={13} />{delivery.location}</span></td><td>{delivery.window}</td><td><span className={`vehicle-pill ${delivery.color}`}><i />{delivery.vehicle}</span></td><td>{delivery.load}</td><td><span className="status-pill"><i />{delivery.status}</span></td><td><button className="row-more" aria-label={`More for ${delivery.id}`}><MoreHorizontal size={17} /></button></td></tr>)}</tbody></table>{visibleDeliveries.length === 0 && <div className="empty-search">No deliveries match “{query}”.</div>}</div>
            <div className="table-footer"><span>Showing <b>{visibleDeliveries.length}</b> of 8 deliveries <span className="footer-separator">·</span> Scenario: <b>Micro fixture</b></span><button className="text-link" onClick={() => setQuery('')}>Clear filters <X size={13} /></button></div>
          </section>

          <footer className="page-footer"><span>ReRoute <b>·</b> Hackathon demo</span><span>Plans shown are illustrative local data <i>·</i> No live maps or GPS</span></footer>
        </div>
      </main>
    </div>
  );
}

function KpiCard({ label, value, unit, detail, icon, trend, trendKind, trendIcon }: { label: string; value: string; unit?: string; detail: string; icon: React.ReactNode; trend: string; trendKind: string; trendIcon?: React.ReactNode }) {
  return <div className="kpi-card"><div className="kpi-top"><span>{label}</span><span className="kpi-icon">{icon}</span></div><div className="kpi-value">{value}<small>{unit}</small></div><div className="kpi-bottom"><span>{detail}</span><span className={`kpi-trend ${trendKind}`}>{trendIcon}{trend}</span></div></div>;
}

function FormField({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="form-field"><span>{label}</span>{children}</label>;
}

function getTimelineLeft(time: string) {
  const [hours, minutes] = time.split(':').map(Number);
  const minutesFromStart = (hours - 8) * 60 + minutes;
  return `${Math.max(0, Math.min(100, minutesFromStart / 150 * 100))}%`;
}

export default App;
