; ModuleID = "meu_modulo.bc"
target triple = "x86_64-unknown-linux-gnu"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"

@"a" = global i32 0, align 4
define i32 @"main"()
{
entry:
  %"ret" = alloca i32, align 4
  store i32 25, i32* @"a"
  %"x_temp" = load i32, i32* @"a"
  %"maior" = icmp sgt i32 %"x_temp", 5
  br i1 %"maior", label %"iftrue_1", label %"iffalse_1"
iftrue_1:
  %"x_temp.1" = load i32, i32* @"a"
  %"menor" = icmp slt i32 %"x_temp.1", 20
  br i1 %"menor", label %"iftrue_1.1", label %"iffalse_1.1"
iffalse_1:
  store i32 0, i32* %"ret"
  br label %"ifend_1"
ifend_1:
  %"x_temp.2" = load i32, i32* %"ret"
  ret i32 %"x_temp.2"
iftrue_1.1:
  store i32 1, i32* %"ret"
  br label %"ifend_1.1"
iffalse_1.1:
  store i32 2, i32* %"ret"
  br label %"ifend_1.1"
ifend_1.1:
  br label %"ifend_1"
}
