import { WorkspaceLayout } from "./WorkspaceLayout";

export function HiringManagerLayout() {
  const navLinks = [
    {
      to: "/hm/shared-campaigns",
      label: "Shared Campaigns",
      icon: (
        <svg className="w-5 h-5 mr-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
    },
    {
      to: "/hm/profile",
      label: "Profile",
      icon: (
        <svg className="w-5 h-5 mr-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      ),
    },
  ];

  return (
    <WorkspaceLayout
      navLinks={navLinks}
      portalName="Hiring Manager Portal"
      workspaceName="Hiring Manager Workspace"
    />
  );
}
