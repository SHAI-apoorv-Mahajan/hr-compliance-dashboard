"""Employee directory + inline email edit. FR-020 / US-021."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import AppUser, SilverEmployee
from routers.deps import get_current_user
from schemas.employees import EmailUpdate, EmployeeOut


router = APIRouter(prefix="/api/v1/employees", tags=["employees"])


@router.get("", response_model=list[EmployeeOut])
def list_employees(
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> list[SilverEmployee]:
    return db.query(SilverEmployee).order_by(SilverEmployee.name).all()


@router.get("/{emp_code}", response_model=EmployeeOut)
def get_employee(
    emp_code: str,
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> SilverEmployee:
    emp = db.query(SilverEmployee).filter(SilverEmployee.emp_code == emp_code).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.patch("/{emp_code}/email", response_model=EmployeeOut)
def update_email(
    emp_code: str,
    payload: EmailUpdate,
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> SilverEmployee:
    emp = db.query(SilverEmployee).filter(SilverEmployee.emp_code == emp_code).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    emp.email = str(payload.email)
    db.commit()
    db.refresh(emp)
    return emp
