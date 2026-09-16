from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from src.api.dependencies import get_risk_service
from src.api.schemas import BlastRadiusResponse, CompanyExposureResponse, RiskHistoryResponse, RiskSummary
from src.api.services.risk import RiskAnalyticsService

router=APIRouter(prefix="/risk",tags=["risk"])
RiskService=Annotated[RiskAnalyticsService,Depends(get_risk_service)]

def _ensure_company_exists(company_id:str,service:RiskAnalyticsService)->None:
    if not service.company_exists(company_id): raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Company '{company_id}' was not found.")

@router.get("/{company_id}",response_model=RiskSummary,summary="Get current aggregate company risk")
def get_company_risk(company_id:str,service:RiskService,max_hops:Annotated[int,Query(ge=1,le=3)]=3)->RiskSummary:
    _ensure_company_exists(company_id,service); return RiskSummary(**service.get_company_risk(company_id,max_hops=max_hops))

@router.get("/{company_id}/history",response_model=RiskHistoryResponse,summary="Get historical aggregate company risk")
def get_risk_history(company_id:str,service:RiskService,max_hops:Annotated[int,Query(ge=1,le=3)]=3,limit:Annotated[int,Query(ge=1,le=500)]=100)->RiskHistoryResponse:
    _ensure_company_exists(company_id,service); return RiskHistoryResponse(**service.get_risk_history(company_id,max_hops=max_hops,limit=limit))

@router.get("/{company_id}/blast-radius",response_model=BlastRadiusResponse,summary="Get downstream blast radius")
def get_blast_radius(company_id:str,service:RiskService,max_hops:Annotated[int,Query(ge=1,le=3)]=3)->BlastRadiusResponse:
    _ensure_company_exists(company_id,service); return BlastRadiusResponse(**service.get_blast_radius(company_id,max_hops=max_hops))

@router.get("/{company_id}/exposure",response_model=CompanyExposureResponse,summary="Get upstream event exposure")
def get_company_exposure(company_id:str,service:RiskService,max_hops:Annotated[int,Query(ge=1,le=3)]=3)->CompanyExposureResponse:
    _ensure_company_exists(company_id,service); return CompanyExposureResponse(**service.get_exposure(company_id,max_hops=max_hops))
