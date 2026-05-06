import SubRolLayout from "@/components/SubRolLayout";

export default function VisorLayout({ children }: { children: React.ReactNode }) {
  return <SubRolLayout allowed={["visor"]}>{children}</SubRolLayout>;
}
