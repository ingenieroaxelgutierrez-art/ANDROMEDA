import SubRolLayout from "@/components/SubRolLayout";

export default function AlmaceneroLayout({ children }: { children: React.ReactNode }) {
  return <SubRolLayout allowed={["almacenero"]}>{children}</SubRolLayout>;
}
