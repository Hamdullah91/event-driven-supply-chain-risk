from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.dependencies import get_company_service
from src.api.schemas import CompanyDetail, CompanyListResponse, CompanyNetwork
from src.api.services.companies import CompanyGraphService


router = APIRouter(prefix="/companies", tags=["companies"])
CompanyService = Annotated[CompanyGraphService, Depends(get_company_service)]


@router.get("", response_model=CompanyListResponse, summary="List companies")
def list_companies(
    service: CompanyService,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CompanyListResponse:
    return CompanyListResponse(**service.list_companies(limit=limit, offset=offset))


@router.get("/{company_id}", response_model=CompanyDetail, summary="Get company details")
def get_company(company_id: str, service: CompanyService) -> CompanyDetail:
    company = service.get_company(company_id)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company '{company_id}' was not found.",
        )
    return CompanyDetail(**company)


@router.get(
    "/{company_id}/network",
    response_model=CompanyNetwork,
    summary="Get a bounded company graph neighbourhood",
)
def get_company_network(
    company_id: str,
    service: CompanyService,
    depth: Annotated[int, Query(ge=1, le=3)] = 2,
) -> CompanyNetwork:
    network = service.get_company_network(company_id, depth=depth)
    if network is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company '{company_id}' was not found.",
        )
    return CompanyNetwork(**network)
