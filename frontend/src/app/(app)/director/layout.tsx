import SubRolLayout from "@/components/SubRolLayout";

export default function DirectorLayout({ children }: { children: React.ReactNode }) {
  return <SubRolLayout allowed={["director"]}>{children}</SubRolLayout>;
}
