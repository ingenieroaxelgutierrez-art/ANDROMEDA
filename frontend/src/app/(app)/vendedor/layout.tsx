import SubRolLayout from "@/components/SubRolLayout";

export default function VendedorLayout({ children }: { children: React.ReactNode }) {
  return <SubRolLayout allowed={["vendedor"]}>{children}</SubRolLayout>;
}
