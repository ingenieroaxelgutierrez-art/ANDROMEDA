import SubRolLayout from "@/components/SubRolLayout";

export default function CoordinadorLayout({ children }: { children: React.ReactNode }) {
  return <SubRolLayout allowed={["coordinador"]}>{children}</SubRolLayout>;
}
