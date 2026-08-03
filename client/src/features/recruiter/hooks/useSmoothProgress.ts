import { useEffect, useState } from "react";
import { RECRUITER_STAGES } from "../utils/recruiterTerms";

export function useSmoothProgress(stage: string | undefined, status: string | undefined) {
  const [percent, setPercent] = useState(0);

  const stageUpper = stage?.toUpperCase() || "QUEUED";
  const statusUpper = status?.toUpperCase() || "PENDING";
  const isFailed = statusUpper === "FAILED";
  const isSuccess = statusUpper === "SUCCESS" || stageUpper === "COMPLETED";

  const stageConfig = RECRUITER_STAGES[stageUpper] || { percent: 10 };
  const targetMax = isSuccess ? 100 : (isFailed ? percent : stageConfig.percent);

  useEffect(() => {
    if (isFailed) return;

    if (isSuccess) {
      const interval = setInterval(() => {
        setPercent((prev) => {
          if (prev >= 100) {
            clearInterval(interval);
            return 100;
          }
          const step = (100 - prev) * 0.15 + 0.5;
          return Math.min(prev + step, 100);
        });
      }, 80);
      return () => clearInterval(interval);
    }

    // Active matching: increment gradually
    const interval = setInterval(() => {
      setPercent((prev) => {
        const minVal = stageConfig.percent - 15 >= 0 ? stageConfig.percent - 15 : 0;
        let val = Math.max(prev, minVal);

        const distance = targetMax - val;
        if (distance > 0.01) {
          const step = Math.max(distance * 0.04, 0.05);
          val = Math.min(val + step, targetMax - 0.1);
        }
        return val;
      });
    }, 150);

    return () => clearInterval(interval);
  }, [targetMax, isSuccess, isFailed, stageConfig.percent]);

  return Math.round(percent * 10) / 10;
}
