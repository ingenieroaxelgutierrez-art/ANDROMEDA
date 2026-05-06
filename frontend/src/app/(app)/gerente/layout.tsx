import SubRolLayout from "@/components/SubRolLayout";

export default function GerenteLayout({ children }: { children: React.ReactNode }) {
  return <SubRolLayout allowed={["gerente"]}>{children}</SubRolLayout>;
}
