import SubRolLayout from "@/components/SubRolLayout";

export default function JefeLayout({ children }: { children: React.ReactNode }) {
  return <SubRolLayout allowed={["jefe"]}>{children}</SubRolLayout>;
}
