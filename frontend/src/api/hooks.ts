import { useEffect, useState } from "react";
import { api, Plan, Scenario, ValidationReport } from "./client";

export function useInitialPlan(scenarioName: string) {
  const [data, setData] = useState<{ scenario: Scenario; plan: Plan; report: ValidationReport }>();
  const [error, setError] = useState<Error>();
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(undefined);
    Promise.all([api.scenario(scenarioName), api.initialPlan(scenarioName)])
      .then(([scenario, result]) => active && setData({ scenario, plan: result.plan, report: result.validation_report }))
      .catch((reason: unknown) => active && setError(reason instanceof Error ? reason : new Error("Unable to load plan")))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [scenarioName]);
  return { data, error, loading };
}