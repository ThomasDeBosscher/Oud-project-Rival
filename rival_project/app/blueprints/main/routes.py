from flask import render_template, Blueprint, request, redirect, url_for, flash, session
from app.extensions import db
from app.models.company import Company
from app.models.finance import CompanyFinance
from app.models.watchlist import Watchlist
from .forms import CompanyForm, QuickAddForm, TickerForm
from urllib.parse import urlparse
from typing import Optional


def _normalize_url(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    u = raw.strip()
    if not u:
        return None
    if not (u.startswith('http://') or u.startswith('https://')):
        u = 'https://' + u
    parsed = urlparse(u)
    netloc = parsed.netloc.lower()
    # strip common www.
    if netloc.startswith('www.'):
        netloc = netloc[4:]
    # Rebuild as scheme://netloc (drop path/query for canonical storage)
    return f"{parsed.scheme}://{netloc}"

bp = Blueprint('main', __name__, template_folder='templates')

@bp.route('/')
def index():
    quick_form = QuickAddForm()
    return render_template('index.html', quick_form=quick_form)

@bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@bp.route('/company/<int:company_id>')
def company_detail(company_id):
    company = Company.query.get_or_404(company_id)
    # Load or refresh finance snapshot
    snap = CompanyFinance.query.filter_by(company_id=company.id).first()
    if not snap or snap.is_stale:
        try:
            from app.services.scraping.finance import resolve_and_fetch
            ticker, data = resolve_and_fetch(company.name, company.url)
        except Exception:
            ticker, data = None, None
        if data:
            if not snap:
                snap = CompanyFinance(company_id=company.id)
                db.session.add(snap)
            snap.ticker = ticker
            snap.currency = data.get('currency')
            snap.price = data.get('price')
            snap.market_cap = data.get('market_cap')
            snap.pe_ratio = data.get('pe_ratio')
            snap.revenue = data.get('revenue')
            snap.employees = data.get('employees')
            from datetime import datetime
            snap.updated_at = datetime.utcnow()
            db.session.commit()
            # attach non-persistent change metrics for template usage
            snap.change_percent = data.get('change_percent')
            snap.change = data.get('change')

    # Even if not stale, try to compute transient change metrics from current market data
    if snap and getattr(snap, 'change_percent', None) is None and snap.ticker:
        try:
            from app.services.scraping.finance import fetch_financials
            tmp = fetch_financials(snap.ticker)
            if tmp:
                snap.change_percent = tmp.get('change_percent')
                snap.change = tmp.get('change')
        except Exception:
            pass
    ticker_form = TickerForm()
    if snap and snap.ticker:
        ticker_form.ticker.data = snap.ticker
    return render_template('company_detail.html', company=company, finance=snap, ticker_form=ticker_form)


@bp.route('/company/<int:company_id>/set-ticker', methods=['POST'])
def set_company_ticker(company_id):
    company = Company.query.get_or_404(company_id)
    form = TickerForm()
    if not form.validate_on_submit():
        for e in form.ticker.errors:
            flash(e, 'danger')
        return redirect(url_for('main.company_detail', company_id=company.id))

    ticker = (form.ticker.data or '').strip().upper()
    if not ticker:
        flash('Ticker cannot be empty.', 'danger')
        return redirect(url_for('main.company_detail', company_id=company.id))

    # Ensure snapshot exists
    snap = CompanyFinance.query.filter_by(company_id=company.id).first()
    if not snap:
        snap = CompanyFinance(company_id=company.id)
        db.session.add(snap)
        db.session.commit()

    # Fetch data for provided ticker
    try:
        from app.services.scraping.finance import fetch_financials
        data = fetch_financials(ticker)
    except Exception:
        data = None

    if not data:
        flash('Could not fetch financials for given ticker.', 'danger')
        return redirect(url_for('main.company_detail', company_id=company.id))

    from datetime import datetime
    snap.ticker = ticker
    snap.currency = data.get('currency')
    snap.price = data.get('price')
    snap.market_cap = data.get('market_cap')
    snap.pe_ratio = data.get('pe_ratio')
    snap.revenue = data.get('revenue')
    snap.employees = data.get('employees')
    snap.updated_at = datetime.utcnow()
    db.session.commit()

    flash('Ticker saved and financials updated.', 'success')
    return redirect(url_for('main.company_detail', company_id=company.id))

@bp.route('/compare')
def compare():
    companies = Company.query.order_by(Company.name.asc()).all()
    c1_id = request.args.get('item1', type=int)
    c2_id = request.args.get('item2', type=int)
    c1 = Company.query.get(c1_id) if c1_id else None
    c2 = Company.query.get(c2_id) if c2_id else None

    # Ensure finance snapshots exist/fresh enough
    def ensure_fin(c: Company):
        if not c:
            return None
        snap = CompanyFinance.query.filter_by(company_id=c.id).first()
        if not snap or snap.is_stale:
            try:
                from app.services.scraping.finance import resolve_and_fetch
                ticker, data = resolve_and_fetch(c.name, c.url)
            except Exception:
                ticker, data = None, None
            if data:
                if not snap:
                    snap = CompanyFinance(company_id=c.id)
                    db.session.add(snap)
                snap.ticker = ticker
                snap.currency = data.get('currency')
                snap.price = data.get('price')
                snap.market_cap = data.get('market_cap')
                snap.pe_ratio = data.get('pe_ratio')
                snap.revenue = data.get('revenue')
                snap.employees = data.get('employees')
                from datetime import datetime
                snap.updated_at = datetime.utcnow()
                db.session.commit()
                # attach non-persistent change metrics
                snap.change_percent = data.get('change_percent')
                snap.change = data.get('change')
        # Try to attach transient change metrics even if not stale
        if snap and getattr(snap, 'change_percent', None) is None and snap.ticker:
            try:
                from app.services.scraping.finance import fetch_financials
                tmp = fetch_financials(snap.ticker)
                if tmp:
                    snap.change_percent = tmp.get('change_percent')
                    snap.change = tmp.get('change')
            except Exception:
                pass
        return snap

    f1 = ensure_fin(c1) if c1 else None
    f2 = ensure_fin(c2) if c2 else None
    return render_template('compare.html', companies=companies, c1=c1, c2=c2, f1=f1, f2=f2)

@bp.route('/trends')
def trends():
    return render_template('trends.html')

@bp.route('/watchlist')
def watchlist():
    user_id = session.get('user_id')
    if not user_id:
        flash('Log in to view your watchlist.', 'info')
        return redirect(url_for('auth.login'))
    items = (db.session.query(Watchlist)
             .filter_by(user_id=user_id)
             .join(Company, Watchlist.company_id == Company.id)
             .all())
    return render_template('watchlist.html', items=items)

@bp.route('/alerts')
def alerts():
    return render_template('alerts.html')

@bp.route('/settings')
def settings():
    return render_template('settings.html')

@bp.route('/export')
def export():
    return render_template('export.html')

def init_app(app):
    app.register_blueprint(bp)

@bp.route('/companies', methods=['GET', 'POST'])
def companies():
    form = CompanyForm()
    if form.validate_on_submit():
        # Normalize/derive inputs
        name = (form.name.data or '').strip()
        url = _normalize_url(form.url.data)
        if not name and url:
            # derive a readable name from domain
            domain = urlparse(url).netloc
            name = domain.split(':')[0].replace('www.', '')
            # Title-case rough heuristic (keep dots/hyphens spaced)
            name = name.replace('-', ' ').replace('.', ' ').title()

        # Try to find an existing company by URL first, then by name
        existing = None
        if url:
            existing = Company.query.filter(Company.url.ilike(url)).first()
        if not existing and name:
            existing = Company.query.filter(Company.name.ilike(name)).first()

        if existing:
            c = existing
        else:
            c = Company(name=name or 'Unnamed Company', url=url)
            db.session.add(c)
            db.session.commit()

        # Optionally add to watchlist when requested and user logged in
        user_id = session.get('user_id')
        if user_id and form.add_to_watchlist.data:
            link = Watchlist.query.filter_by(user_id=user_id, company_id=c.id).first()
            if not link:
                db.session.add(Watchlist(user_id=user_id, company_id=c.id))
                db.session.commit()
                flash('Added to your watchlist.', 'success')
            else:
                flash('Already in your watchlist.', 'info')
        else:
            flash('Company added.', 'success')

        return redirect(url_for('main.companies'))
    companies = Company.query.order_by(Company.created_at.desc()).all()
    return render_template('companies.html', form=form, companies=companies)


@bp.route('/companies/quick-add', methods=['POST'])
def quick_add_company():
    form = QuickAddForm()
    if not form.validate_on_submit():
        # bounce back to home with messages
        for e in form.url.errors:
            flash(e, 'danger')
        return redirect(url_for('main.index'))

    url = _normalize_url(form.url.data)
    name = None
    if url:
        domain = urlparse(url).netloc
        name = domain.split(':')[0].replace('www.', '')
        name = name.replace('-', ' ').replace('.', ' ').title()

    # find or create
    existing = None
    if url:
        existing = Company.query.filter(Company.url.ilike(url)).first()
    if not existing and name:
        existing = Company.query.filter(Company.name.ilike(name)).first()

    if existing:
        c = existing
    else:
        c = Company(name=name or 'Unnamed Company', url=url)
        db.session.add(c)
        db.session.commit()

    user_id = session.get('user_id')
    if user_id and form.add_to_watchlist.data:
        link = Watchlist.query.filter_by(user_id=user_id, company_id=c.id).first()
        if not link:
            db.session.add(Watchlist(user_id=user_id, company_id=c.id))
            db.session.commit()
            flash('Added to your watchlist.', 'success')
        else:
            flash('Already in your watchlist.', 'info')
        return redirect(url_for('main.watchlist'))

    flash('Company added.', 'success')
    return redirect(url_for('main.companies'))

@bp.route('/watchlist/add/<int:company_id>', methods=['POST'])
def watchlist_add(company_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('Log in to use your watchlist.', 'info')
        return redirect(url_for('auth.login'))
    # Ensure company exists
    company = Company.query.get_or_404(company_id)
    # Upsert-like: ignore if exists
    existing = Watchlist.query.filter_by(user_id=user_id, company_id=company.id).first()
    if existing:
        flash('Already in your watchlist.', 'info')
    else:
        db.session.add(Watchlist(user_id=user_id, company_id=company.id))
        db.session.commit()
        flash('Added to your watchlist.', 'success')
    return redirect(request.referrer or url_for('main.companies'))

@bp.route('/watchlist/remove/<int:item_id>', methods=['POST'])
def watchlist_remove(item_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('Log in to use your watchlist.', 'info')
        return redirect(url_for('auth.login'))
    item = Watchlist.query.get_or_404(item_id)
    if item.user_id != user_id:
        flash('Not allowed.', 'danger')
        return redirect(url_for('main.watchlist'))
    db.session.delete(item)
    db.session.commit()
    flash('Removed from your watchlist.', 'success')
    return redirect(url_for('main.watchlist'))