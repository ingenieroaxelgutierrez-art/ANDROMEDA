import SubRolLayout from "@/components/SubRolLayout";

export default function AuxiliarLayout({ children }: { children: React.ReactNode }) {
  return <SubRolLayout allowed={["auxiliar"]}>{children}</SubRolLayout>;
}
