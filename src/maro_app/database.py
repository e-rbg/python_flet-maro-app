import os
from contextlib import contextmanager
from typing import List, Optional
from datetime import datetime
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload

from src.maro_app.models import (
    Base, MotherTitle, Landowner, IndividualTitle, AgrarianReformBeneficiary,
    Province, Municipality, Barangay
)

# --- Database Setup ---
DB_URL = "sqlite:///maro_app.db"
engine = create_engine(DB_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Initialize database and seed test data if empty."""
    Base.metadata.create_all(bind=engine)

    with get_db_session() as session:
        if session.query(Province).count() == 0:
            p1 = Province(name="Davao de Oro")
            session.add(p1)
            session.flush()

            m1 = Municipality(name="Mabini", province_id=p1.id)
            session.add(m1)
            session.flush()

            b1 = Barangay(name="Dona Alicia", municipality_id=m1.id)
            b2 = Barangay(name="Poblacion", municipality_id=m1.id)
            session.add_all([b1, b2])


@contextmanager
def get_db_session():
    """Context manager to ensure database sessions are cleanly opened and closed."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# --- Internal Helper Utilities ---
def _parse_date(date_input) -> Optional[datetime.date]:
    """Safely normalizes incoming front-end strings or objects into Python date types."""
    if not date_input:
        return None
    if isinstance(date_input, str):
        try:
            return datetime.strptime(date_input.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None
    return date_input


# --- Dashboard Data ---
def get_dashboard_data(search_query: str = "") -> List[dict]:
    """Fetch combined records across Landowners, Mother Titles, Individual Titles, and ARBs."""
    with get_db_session() as session:
        query = (
            session.query(MotherTitle)
            .join(Landowner, MotherTitle.landowner_id == Landowner.id)
            .outerjoin(IndividualTitle, MotherTitle.id == IndividualTitle.mother_title_id)
            .outerjoin(AgrarianReformBeneficiary, IndividualTitle.arb_id == AgrarianReformBeneficiary.id)
        )

        if search_query:
            search_filter = f"%{search_query}%"
            query = query.filter(
                (MotherTitle.title_number.like(search_filter)) |
                (Landowner.name.like(search_filter)) |
                (AgrarianReformBeneficiary.first_name.like(search_filter)) |
                (AgrarianReformBeneficiary.last_name.like(search_filter)) |
                (IndividualTitle.title_number.like(search_filter)) # 👈 You used title_number here!
            )

        results = query.all()

        records = []
        for mt in results:
            if not mt.individual_titles:
                records.append({
                    "landowner": mt.landowner.name,
                    "mother_title": mt.title_number,
                    "mother_area": f"{mt.area_hectares} ha",
                    "individual_title": "—",
                    "allocated_area": "—",
                    "arb": "—"
                })
            else:
                for it in mt.individual_titles:
                    records.append({
                        "landowner": mt.landowner.name,
                        "mother_title": mt.title_number,
                        "mother_area": f"{mt.area_hectares} ha",
                        "individual_title": it.title_number,
                        "allocated_area": f"{it.area} ha",
                        "arb": it.arb.full_name if it.arb else "Unassigned"
                    })
        return records


# --- Location Helpers ---
def get_all_provinces() -> List[Province]:
    with get_db_session() as session:
        res = session.query(Province).order_by(Province.name).all()
        session.expunge_all()  
        return res


def get_all_municipalities_global() -> List[Municipality]:
    with get_db_session() as session:
        res = session.query(Municipality).options(
            joinedload(Municipality.province)
        ).order_by(Municipality.name).all()
        session.expunge_all()  
        return res


def get_all_barangays_global() -> List[Barangay]:
    with get_db_session() as session:
        res = session.query(Barangay).options(
            joinedload(Barangay.municipality).joinedload(Municipality.province)
        ).order_by(Barangay.name).all()
        session.expunge_all()  
        return res


# --- Landowner Core ---
def get_all_landowners() -> List[Landowner]:
    with get_db_session() as session:
        res = session.query(Landowner).order_by(Landowner.name).all()
        session.expunge_all()
        return res


def save_landowner(name: str, contact_info: Optional[str] = None, landowner_id: Optional[int] = None) -> Landowner:
    with get_db_session() as session:
        if landowner_id:
            lo = session.query(Landowner).filter(Landowner.id == landowner_id).first()
            if lo:
                lo.name = name
                lo.contact_info = contact_info
        else:
            lo = Landowner(name=name, contact_info=contact_info)
            session.add(lo)
        session.flush()
        session.refresh(lo)
        session.expunge_all()
        return lo


def delete_landowner(landowner_id: int) -> None:
    with get_db_session() as session:
        lo = session.query(Landowner).filter(Landowner.id == landowner_id).first()
        if lo:
            session.delete(lo)


# --- Mother Title Core ---
def get_all_mother_titles() -> List[MotherTitle]:
    with get_db_session() as session:
        titles = session.query(MotherTitle).options(
            joinedload(MotherTitle.landowner),
            joinedload(MotherTitle.individual_titles).joinedload(IndividualTitle.arb),
            joinedload(MotherTitle.barangay).joinedload(Barangay.municipality).joinedload(Municipality.province)
        ).all()
        session.expunge_all() 
        return titles


def save_mother_title(
    title_number: str, landowner_id: int, area: float, lot_number: str,
    survey_number: str, mode_of_acquisition: str, raw_text: str, lines: str,
    barangay_id: int, title_id: Optional[int] = None
) -> MotherTitle:
    with get_db_session() as session:
        if title_id:
            mt = session.query(MotherTitle).filter(MotherTitle.id == title_id).first()
            if mt:
                mt.title_number = title_number
                mt.landowner_id = landowner_id
                mt.area_hectares = area
                mt.lot_number = lot_number
                mt.survey_number = survey_number
                mt.mode_of_acquisition = mode_of_acquisition
                mt.raw_text = raw_text
                mt.lines = lines
                mt.barangay_id = barangay_id
        else:
            mt = MotherTitle(
                title_number=title_number, landowner_id=landowner_id, area_hectares=area,
                lot_number=lot_number, survey_number=survey_number, mode_of_acquisition=mode_of_acquisition,
                raw_text=raw_text, lines=lines, barangay_id=barangay_id
            )
            session.add(mt)
        session.flush()
        session.refresh(mt)
        session.expunge_all()
        return mt


def delete_mother_title(title_id: int) -> None:
    with get_db_session() as session:
        mt = session.query(MotherTitle).filter(MotherTitle.id == title_id).first()
        if mt:
            session.delete(mt)


# --- Geographic Write Operations ---
def add_province(name: str) -> Province:
    with get_db_session() as session:
        db_prov = Province(name=name)
        session.add(db_prov)
        session.flush()
        session.refresh(db_prov)
        session.expunge_all()
        return db_prov


def add_municipality(name: str, province_id: int) -> Municipality:
    with get_db_session() as session:
        db_mun = Municipality(name=name, province_id=province_id)
        session.add(db_mun)
        session.flush()
        session.refresh(db_mun)
        session.expunge_all()
        return db_mun


def add_barangay(name: str, municipality_id: int) -> Barangay:
    with get_db_session() as session:
        db_bar = Barangay(name=name, municipality_id=municipality_id)
        session.add(db_bar)
        session.flush()
        session.refresh(db_bar)
        session.expunge_all()
        return db_bar


def delete_province(province_id: int) -> None:
    with get_db_session() as session:
        prov = session.query(Province).filter(Province.id == province_id).first()
        if prov:
            session.delete(prov)


def delete_municipality(municipality_id: int) -> None:
    with get_db_session() as session:
        mun = session.query(Municipality).filter(Municipality.id == municipality_id).first()
        if mun:
            session.delete(mun)


def delete_barangay(barangay_id: int) -> None:
    with get_db_session() as session:
        bar = session.query(Barangay).filter(Barangay.id == barangay_id).first()
        if bar:
            session.delete(bar)


# --- Individual/Resultant Titles Core ---
def get_all_individual_titles() -> List[IndividualTitle]:
    """Fetches all Individual splits cleanly decoupled using session wrapper."""
    with get_db_session() as session:
        res = (
            session.query(IndividualTitle)
            .options(joinedload(IndividualTitle.mother_title))
            .all()
        )
        session.expunge_all()
        return res


def save_individual_title(
    title_number: str, mother_title_id: str, cloa_type: str, area: float, 
    survey_number: Optional[str] = None, date_registered = None, 
    date_distributed = None, raw_text: Optional[str] = None, 
    lines: Optional[str] = None, status: str = 'active', 
    title_id: Optional[str] = None
) -> IndividualTitle:
    """Inserts or modifies an Individual title using the consolidated session manager."""
    parsed_reg = _parse_date(date_registered)
    parsed_dist = _parse_date(date_distributed)

    # Cast string representations to clean UUID strings if necessary
    m_title_uuid = str(mother_title_id) if mother_title_id else None

    with get_db_session() as session:
        if title_id:
            rt = session.query(IndividualTitle).filter(IndividualTitle.id == str(title_id)).first()
            if rt:
                rt.title_number = title_number
                rt.mother_title_id = m_title_uuid
                rt.cloa_type = cloa_type
                rt.area = area
                rt.survey_number = survey_number
                rt.date_registered = parsed_reg
                rt.date_distributed = parsed_dist
                rt.raw_text = raw_text
                rt.lines = lines
                rt.status = status
        else:
            rt = IndividualTitle(
                id=str(uuid.uuid4()),
                title_number=title_number,
                mother_title_id=m_title_uuid,
                cloa_type=cloa_type,
                area=area,
                survey_number=survey_number,
                date_registered=parsed_reg,
                date_distributed=parsed_dist,
                raw_text=raw_text,
                lines=lines,
                status=status
            )
            session.add(rt)
        
        session.flush()
        if rt:
            session.refresh(rt)
        session.expunge_all()
        return rt


def delete_individual_title(title_id: str) -> bool:
    """Removes an Individual title tracking marker safely via uniform session contexts."""
    with get_db_session() as session:
        rt = session.query(IndividualTitle).filter(IndividualTitle.id == str(title_id)).first()
        if rt:
            session.delete(rt)
            return True
        return False