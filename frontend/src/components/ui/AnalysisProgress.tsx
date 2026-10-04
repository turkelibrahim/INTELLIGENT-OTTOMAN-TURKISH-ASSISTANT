import type { AnalysisStage } from "@/lib/api";

const STEPS = [
  { key: "UPLOADING",        label: "Hazırlanıyor" },
  { key: "PREPROCESSING",    label: "OCR" },
  { key: "TRANSLITERATION",  label: "Dil Dönüşümü" },
  { key: "ENTITY_ANALYSIS",  label: "Analiz" },
  { key: "COMPLETE",         label: "Tamamlandı" },
] as const;

const STAGE_TO_STEP: Partial<Record<AnalysisStage, number>> = {
  UPLOADING: 0,
  PREPROCESSING: 1,
  OCR: 1,
  TRANSLITERATION: 2,
  MODERNIZATION: 2,
  ENTITY_ANALYSIS: 3,
  HISTORICAL_RAG: 3,
  COMPLETE: 4,
  ERROR: -1,
};

interface AnalysisProgressProps {
  stage: AnalysisStage;
  uploadProgress?: number;
}

export default function AnalysisProgress({ stage, uploadProgress }: AnalysisProgressProps) {
  const activeStep = STAGE_TO_STEP[stage] ?? -1;
  const isError = stage === "ERROR";

  if (isError) {
    return (
      <div className="ota-progress-error" role="alert">
        <span className="ota-progress-error-icon">⚠</span>
        <span>Analiz tamamlanamadı. Lütfen tekrar deneyin.</span>
      </div>
    );
  }

  return (
    <div className="ota-analysis-progress" aria-label="Analiz durumu">
      <div className="ota-progress-steps">
        {STEPS.map((step, i) => {
          const isDone = activeStep > i;
          const isActive = activeStep === i;
          return (
            <div key={step.key} className="ota-progress-step-wrap">
              <div
                className={`ota-progress-step${isDone ? " done" : ""}${isActive ? " active" : ""}`}
                aria-current={isActive ? "step" : undefined}
              >
                <span className="ota-step-dot">
                  {isDone ? "✓" : isActive ? "●" : "○"}
                </span>
                <span className="ota-step-label">{step.label}</span>
                {isActive && stage === "UPLOADING" && typeof uploadProgress === "number" && (
                  <span className="ota-step-sub">%{uploadProgress}</span>
                )}
              </div>
              {i < STEPS.length - 1 && (
                <div className={`ota-step-connector${isDone ? " done" : ""}`} aria-hidden="true" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
