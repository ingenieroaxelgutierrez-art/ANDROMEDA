import SubRolLayout from "@/components/SubRolLayout";

export default function TiendaLayout({ children }: { children: React.ReactNode }) {
  return <SubRolLayout allowed={["tienda"]}>{children}</SubRolLayout>;
}
