from __future__ import annotations

from src.risk.aggregation import RiskContribution, aggregate_company_risk
from src.risk.mathematics import calculate_path_risk
from src.risk.repository import RiskRepository
from src.risk.scoring import severity_to_initial_risk


class RiskAnalyticsService:
    """Application service for graph-grounded risk analytics APIs."""
    def __init__(self, repository: RiskRepository) -> None: self.repository = repository
    def company_exists(self, company_id: str) -> bool: return self.repository.company_exists(company_id)
    def event_exists(self, event_id: str) -> bool: return self.repository.event_exists(event_id)

    @staticmethod
    def _path_risk(severity: str, hop_distance: int, weights: list[float]) -> tuple[float, float, float, float]:
        initial_risk = severity_to_initial_risk(severity)
        if hop_distance == 0: return initial_risk, 1.0, 1.0, initial_risk
        result = calculate_path_risk(initial_risk=initial_risk, dependency_weights=weights)
        return initial_risk, result.path_dependency, result.distance_decay, result.propagated_risk

    def get_event_blast_radius(self, event_id: str, *, max_hops: int = 3) -> dict:
        rows = self.repository.get_event_blast_radius(event_id, max_hops=max_hops); strongest_by_company = {}; event_type = None; severity = None
        for row in rows:
            event_type=row.get("event_type"); severity=str(row["severity"]); hop=int(row["hop_distance"]); weights=[float(w) for w in (row["dependency_weights"] or [])]
            initial, dependency, decay, risk=self._path_risk(severity, hop, weights); target=str(row["target_company_id"])
            candidate={"company_id":target,"company_name":str(row["target_company_name"]),"origin_company_id":str(row["affected_company_id"]),"origin_company_name":str(row["affected_company_name"]),"hop_distance":hop,"initial_risk":initial,"path_dependency":dependency,"distance_decay":decay,"propagated_risk":risk,"path":list(row.get("path_nodes") or [])}
            if target not in strongest_by_company or risk > strongest_by_company[target]["propagated_risk"]: strongest_by_company[target]=candidate
        companies=sorted(strongest_by_company.values(),key=lambda x:(x["hop_distance"],-x["propagated_risk"],x["company_id"])); hop_counts={str(h):sum(1 for c in companies if c["hop_distance"]==h) for h in range(max_hops+1)}
        return {"event_id":event_id,"event_type":event_type,"severity":severity,"max_hops":max_hops,"affected_company_count":len(companies),"hop_counts":hop_counts,"companies":companies}

    def get_blast_radius(self, company_id: str, *, max_hops: int = 3) -> dict:
        rows=self.repository.get_company_blast_radius(company_id,max_hops=max_hops); strongest={}
        for row in rows:
            weights=[float(i["dependency_weight"]) for i in (row["path_relationships"] or [])]; result=calculate_path_risk(initial_risk=1.0,dependency_weights=weights); target=str(row["target_company_id"])
            candidate={"company_id":target,"company_name":str(row["target_company_name"]),"hop_distance":int(row["hop_distance"]),"transmission_factor":result.propagated_risk,"path":list(row["path_nodes"] or [])}
            if target not in strongest or candidate["transmission_factor"] > strongest[target]["transmission_factor"]: strongest[target]=candidate
        companies=sorted(strongest.values(),key=lambda x:(x["hop_distance"],-x["transmission_factor"],x["company_id"])); hops={str(h):sum(1 for c in companies if c["hop_distance"]==h) for h in range(1,max_hops+1)}
        return {"company_id":company_id,"max_hops":max_hops,"affected_company_count":len(companies),"hop_counts":hops,"companies":companies}

    def get_exposure(self, company_id: str, *, max_hops: int = 3) -> dict:
        rows=self.repository.get_company_event_exposure(company_id,max_hops=max_hops); exposures=[]
        for row in rows:
            severity=str(row["severity"]); hop=int(row["hop_distance"]); weights=[float(w) for w in (row["dependency_weights"] or [])]; initial,dependency,decay,risk=self._path_risk(severity,hop,weights)
            exposures.append({"event_id":str(row["event_id"]),"event_type":row.get("event_type"),"severity":severity,"timestamp":row.get("timestamp"),"source":row.get("source"),"confidence":row.get("confidence"),"description":row.get("description"),"affected_company_id":str(row["affected_company_id"]),"affected_company_name":str(row["affected_company_name"]),"hop_distance":hop,"initial_risk":initial,"path_dependency":dependency,"distance_decay":decay,"propagated_risk":risk,"path":list(row.get("path_nodes") or [])})
        exposures.sort(key=lambda x:(-x["propagated_risk"],x["hop_distance"],x["event_id"])); return {"company_id":company_id,"event_count":len({x["event_id"] for x in exposures}),"exposures":exposures}

    @staticmethod
    def _risk_level(score: float) -> str:
        if score >= .75: return "CRITICAL"
        if score >= .50: return "HIGH"
        if score >= .25: return "MEDIUM"
        if score > 0: return "LOW"
        return "NONE"

    def get_company_risk(self, company_id: str, *, max_hops: int = 3) -> dict:
        exposure=self.get_exposure(company_id,max_hops=max_hops); strongest={}
        for item in exposure["exposures"]: strongest[str(item["event_id"])]=max(float(item["propagated_risk"]),strongest.get(str(item["event_id"]),0.0))
        agg=aggregate_company_risk(company_id=company_id,contributions=[RiskContribution(event_id=e,propagated_risk=r) for e,r in sorted(strongest.items())]); score=agg.aggregate_risk
        return {"company_id":company_id,"risk_score":score,"risk_level":self._risk_level(score),"contributing_event_count":agg.event_count,"max_hops":max_hops}

    def get_risk_history(self, company_id: str, *, max_hops: int = 3, limit: int = 100) -> dict:
        rows=self.repository.get_company_risk_history(company_id,max_hops=max_hops,limit=limit); strongest={}; points=[]
        for row in rows:
            event_id=str(row["event_id"]); severity=str(row["severity"]); hop=int(row["hop_distance"]); weights=[float(w) for w in (row["dependency_weights"] or [])]
            _,_,_,risk=self._path_risk(severity,hop,weights); strongest[event_id]=max(risk,strongest.get(event_id,0.0))
            agg=aggregate_company_risk(company_id=company_id,contributions=[RiskContribution(event_id=e,propagated_risk=r) for e,r in sorted(strongest.items())])
            points.append({"timestamp":row["timestamp"],"risk_score":agg.aggregate_risk,"risk_level":self._risk_level(agg.aggregate_risk),"event_id":event_id})
        return {"company_id":company_id,"max_hops":max_hops,"points":points,"count":len(points)}
