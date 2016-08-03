#include "test.h"

struct {
    int abc;
    int def;
    struct {
        int fgh;
    };
} name;

typedef struct x {
    int x1;
    int x2;
} tX;

typedef struct S {
    int member;
    float Member;

    tX x;

    struct {
        int a;
        struct {
            int aa;
        };
        struct {
            int aaa;
            int aaaa;
        } internA;
    };

    struct {
        int b;
        struct {
            int bb;
        };
        struct {
            int bbb;
        } internA;
    } intern;

    struct i {
        int c;
    };

    struct I2 {
        int d;
        int d2;
    } intern2;

    struct I3 {
        int e;
    };
    struct I3 intern3;
} tS;

struct tag {
    int a;
    int b;
};

typedef union U {
    int abc;

    tX x;

    union {
        int a;
        union {
            int aa;
        };
        union {
            int aaa;
            int aaaa;
        } internA;
    };

    union {
        int b;
        union {
            int bb;
        };
        union {
            int bbb;
        } internA;
    } intern;

    union Ia {
        int d;
        int d2;
    } intern2;

    union Ib {
        int e;
        int f;
    };
    union Ib intern3;
} tU;

// TODO: convert this file into regression
// TODO: multiple files with same struct tags (either explicit or anon) are mixed up

int main(int argc, char const *argv[])
{
    tS mystruct;
    tU myunion;
    struct tag var;
    tX myX;

    var.a = 0;

////////////////////////////////////////////////////////////////////////////

    name.fgh = 0;

////////////////////////////////////////////////////////////////////////////

    mystruct.a = 1;
    mystruct.aa = 1;
    mystruct.intern.b = 2;
    // mystruct.c = 3;
    mystruct.intern2.d = 4;
    mystruct.Member = 1;
    mystruct.member = 2;

////////////////////////////////////////////////////////////////////////////

    return 0;
}
