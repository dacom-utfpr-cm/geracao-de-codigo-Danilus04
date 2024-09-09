; ModuleID = "meu_modulo.bc"
target triple = "x86_64-unknown-linux-gnu"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"

declare i32 @"leiaInteiro"()

declare void @"escrevaInteiro"(i32 %".1")

define i32 @"soma"(i32 %"x", i32 %"y")
{
entry:
  %"soma" = add i32 %"x", %"y"
  ret i32 %"soma"
exit:
}

define i32 @"sub"(i32 %"z", i32 %"t")
{
entry:
  %"subtracao" = sub i32 %"z", %"t"
  ret i32 %"subtracao"
exit:
}

define i32 @"principal"()
{
entry:
  %"a" = alloca i32, align 4
  %"b" = alloca i32, align 4
  %"c" = alloca i32, align 4
  %"i" = alloca i32, align 4
  store i32 0.0, i32* %"i"
  br label %"loop"
exit:
loop:
  %".4" = call i32 @"leiaInteiro"()
  store i32 %".4", i32* %"a"
  %".6" = call i32 @"leiaInteiro"()
  store i32 %".6", i32* %"b"
  %"x_temp" = load i32, i32* %"b"
  %"x_temp.1" = load i32, i32* %"a"
  %".8" = call i32 @"sub"(i32 %"x_temp.1", i32 %"x_temp")
  %"x_temp.2" = load i32, i32* %"b"
  %"x_temp.3" = load i32, i32* %"a"
  %".9" = call i32 @"soma"(i32 %"x_temp.3", i32 %"x_temp.2")
  %".10" = call i32 @"soma"(i32 %".9", i32 %".8")
  store i32 %".10", i32* %"c"
  %"x_temp.4" = load i32, i32* %"c"
  call void @"escrevaInteiro"(i32 %"x_temp.4")
  %"x_temp.5" = load i32, i32* %"i"
  %"soma" = add i32 %"x_temp.5", 1.0
  store i32 %"soma", i32* %"i"
  br label %"loop_val"
loop_val:
  %"x_temp.6" = load i32, i32* %"i"
  %"igual" = icmp eq i32 %"x_temp.6", 5.0
  br i1 %"igual", label %"loop", label %"loop_end"
loop_end:
  ret i32 0.0
}
