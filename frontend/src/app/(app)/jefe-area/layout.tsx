import SubRolLayout from "@/components/SubRolLayout";

export default function JefeAreaLayout({ children }: { children: React.ReactNode }) {
  return <SubRolLayout allowed={["jefe_area"]}>{children}</SubRolLayout>;
}
