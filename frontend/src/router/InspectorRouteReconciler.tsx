import { useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";

import { useUiStore } from "../state/uiStore";
import {
  inspectorRouteContextFromLocation,
  isInspectorCompatibleWithTransition,
  type InspectorRouteContext,
} from "./inspectorRoute";

export function InspectorRouteReconciler() {
  const location = useLocation();
  const clearSelection = useUiStore((state) => state.clearSelection);
  const previousRoute = useRef<InspectorRouteContext | null>(null);

  useEffect(() => {
    const nextRoute = inspectorRouteContextFromLocation(location.pathname, location.search);
    const previous = previousRoute.current;
    previousRoute.current = nextRoute;

    if (!previous) return;

    const inspector = useUiStore.getState().inspectorRef;
    if (inspector && !isInspectorCompatibleWithTransition(inspector, previous, nextRoute)) {
      clearSelection();
    }
  }, [clearSelection, location.pathname, location.search]);

  return null;
}
