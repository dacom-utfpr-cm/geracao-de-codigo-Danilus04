; ModuleID = "meu_modulo.bc"
target triple = "x86_64-unknown-linux-gnu"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"

@"b" = global i32 0, align 4
@"a" = global i32 0, align 4
define i32 @"principal"()
{
entry:
  %"c" = alloca i32, align 4
  store i32 10.0, i32* @"a"
  store i32 20.0, i32* @"b"
  %"x_temp" = load i32, i32* @"a"
  %"y_temp" = load i32, i32* @"b"
  %"soma" = add i32 %"x_temp", %"y_temp"
  store i32 %"soma", i32* %"c"
  %"x_temp.1" = load i32, i32* %"c"
  ret i32 %"x_temp.1"
exit:
}
