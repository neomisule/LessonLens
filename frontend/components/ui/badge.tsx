import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils/cn";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default: "border-lens-purple/30 bg-lens-purple/15 text-lens-purple-light",
        secondary: "border-secondary/30 bg-secondary/15 text-secondary",
        accent: "border-lens-teal/30 bg-lens-teal/15 text-lens-teal-light",
        outline: "border-lens-glass-border bg-transparent text-muted-foreground",
        destructive: "border-destructive/30 bg-destructive/15 text-red-400",
        success: "border-green-500/30 bg-green-500/15 text-green-400",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
