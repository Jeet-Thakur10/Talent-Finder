import { useParams } from "react-router-dom";
import { JobDescriptionCreatePage } from "./JobDescriptionCreatePage";

export function JobDescriptionEditPage() {
  const { jobDescriptionId } = useParams<{ jobDescriptionId: string }>();

  return (
    <JobDescriptionCreatePage
      isEdit={true}
      jobDescriptionId={jobDescriptionId}
    />
  );
}

