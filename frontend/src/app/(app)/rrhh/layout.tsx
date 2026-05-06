import SubRolLayout from "@/components/SubRolLayout";

export default function RrhhLayout({ children }: { children: React.ReactNode }) {
  return <SubRolLayout allowed={["rrhh"]}>{children}</SubRolLayout>;
}
