import SubRolLayout from "@/components/SubRolLayout";

export default function ContadorLayout({ children }: { children: React.ReactNode }) {
  return <SubRolLayout allowed={["contador"]}>{children}</SubRolLayout>;
}
