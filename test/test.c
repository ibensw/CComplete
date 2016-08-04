#include "test.h"

/******************************************************************************
 * Anon naming overlap - must be first
 ******************************************************************************/

struct {
    int abc1;
    int def1;
    struct {
        int fgh1;
    };
} name1;

/******************************************************************************
 * Root struct
 ******************************************************************************/

typedef struct rootStructA {
    int a1;
    int a2;
} tA;
tA a_s_var;
struct rootStructA a2_s_var;

typedef struct { // rootStructB
    int b1;
    int b2;
} tB;
tB b_s_var;

struct rootStructC {
    int c1;
    int c2;
};
struct rootStructC c_s_var;

struct { // rootStructD
    int d1;
    int d2;
} d_s_var;

struct {
    int e1;
    int e2;
};

/******************************************************************************
 * Root union
 ******************************************************************************/

typedef union rootUnionA {
    int a1;
    int a2;
} uA;
uA a_u_var;
union rootUnionA a2_u_var;

typedef union { // rootUnionB
    int b1;
    int b2;
} uB;
uB b_u_var;

union rootUnionC {
    int c1;
    int c2;
};
union rootUnionC c_u_var;

union { // rootUnionD
    int d1;
    int d2;
} d_u_var;

union {
    int e1;
    int e2;
};

/******************************************************************************
 * Nested struct + union in struct
 ******************************************************************************/

struct s {
    int member;

    tA a1;
    tB b1;
    struct rootStructC c1;

    uA a2;
    uB b2;
    union rootUnionC c2;

    struct {
        int mem1;
        struct {
            int mem2;
        };
        struct {
            int mem3;
        } internA;
        struct i1 {
            int mem4;
        };
        struct i1 mem5;
        struct i2 {
            int mem6;
        } internB;
        struct i3 {
            int mem7;
        };
    };

    struct {
        int mem8;
        struct {
            int mem9;
        };
        struct {
            int mem10;
        } internA;
        struct i4 {
            int mem11;
        };
        struct i4 mem12;
        struct i5 {
            int mem13;
        } internB;
        struct i6 {
            int mem14;
        };
    } member1;

    struct isa {
        int mem15;
        struct {
            int mem16;
        };
        struct {
            int mem17;
        } internA;
        struct i7 {
            int mem18;
        };
        struct i7 mem19;
        struct i8 {
            int mem20;
        } internB;
        struct i9 {
            int mem21;
        };
    };
    struct isa member2;

    struct isb {
        int mem22;
        struct {
            int mem23;
        };
        struct {
            int mem24;
        } internA;
        struct i10 {
            int mem25;
        };
        struct i10 mem26;
        struct i11 {
            int mem27;
        } internB;
        struct i12 {
            int mem28;
        };
    } member3;

    struct isc { // unreachable
        int mem29;
        struct {
            int mem30;
        };
        struct {
            int mem31;
        } internA;
        struct i13 {
            int mem32;
        };
        struct i13 mem33;
        struct i14 {
            int mem34;
        } internB;
        struct i15 {
            int mem35;
        };
    };

    /*****/

    union {
        int mem36;
        struct {
            int mem37;
        };
        struct {
            int mem38;
        } internA;
        struct i16 {
            int mem39;
        };
        struct i16 mem40;
        struct i17 {
            int mem41;
        } internB;
        struct i18 {
            int mem42;
        };
    };

    union {
        int mem43;
        struct {
            int mem44;
        };
        struct {
            int mem45;
        } internA;
        struct i19 {
            int mem46;
        };
        struct i19 mem47;
        struct i20 {
            int mem48;
        } internB;
        struct i21 {
            int mem49;
        };
    } member4;

    union iua {
        int mem50;
        struct {
            int mem51;
        };
        struct {
            int mem52;
        } internA;
        struct i22 {
            int mem53;
        };
        struct i22 mem54;
        struct i23 {
            int mem55;
        } internB;
        struct i24 {
            int mem56;
        };
    };
    union iua member5;

    union iub {
        int mem57;
        struct {
            int mem58;
        };
        struct {
            int mem59;
        } internA;
        struct i25 {
            int mem60;
        };
        struct i25 mem61;
        struct i26 {
            int mem62;
        } internB;
        struct i27 {
            int mem63;
        };
    } member6;

    union iuc { // unreachable
        int mem64;
        struct {
            int mem65;
        };
        struct {
            int mem66;
        } internA;
        struct i28 {
            int mem67;
        };
        struct i28 mem68;
        struct i29 {
            int mem69;
        } internB;
        struct i30 {
            int mem70;
        };
    };
};

/******************************************************************************
 * Nested struct + union in union
 ******************************************************************************/

union u {
    int member;

    tA a1;
    tB b1;
    struct rootStructC c1;

    uA a2;
    uB b2;
    union rootUnionC c2;

    struct {
        int mem1;
        struct {
            int mem2;
        };
        struct {
            int mem3;
        } internA;
        struct i31 {
            int mem4;
        };
        struct i31 mem5;
        struct i32 {
            int mem6;
        } internB;
        struct i33 {
            int mem7;
        };
    };

    struct {
        int mem8;
        struct {
            int mem9;
        };
        struct {
            int mem10;
        } internA;
        struct i34 {
            int mem11;
        };
        struct i34 mem12;
        struct i35 {
            int mem13;
        } internB;
        struct i36 {
            int mem14;
        };
    } member1;

    struct isd {
        int mem15;
        struct {
            int mem16;
        };
        struct {
            int mem17;
        } internA;
        struct i37 {
            int mem18;
        };
        struct i37 mem19;
        struct i38 {
            int mem20;
        } internB;
        struct i39 {
            int mem21;
        };
    };
    struct isa member2;

    struct ise {
        int mem22;
        struct {
            int mem23;
        };
        struct {
            int mem24;
        } internA;
        struct i40 {
            int mem25;
        };
        struct i40 mem26;
        struct i41 {
            int mem27;
        } internB;
        struct i42 {
            int mem28;
        };
    } member3;

    struct isf { // unreachable
        int mem29;
        struct {
            int mem30;
        };
        struct {
            int mem31;
        } internA;
        struct i43 {
            int mem32;
        };
        struct i43 mem33;
        struct i44 {
            int mem34;
        } internB;
        struct i45 {
            int mem35;
        };
    };

    /*****/

    union {
        int mem36;
        struct {
            int mem37;
        };
        struct {
            int mem38;
        } internA;
        struct i46 {
            int mem39;
        };
        struct i46 mem40;
        struct i47 {
            int mem41;
        } internB;
        struct i48 {
            int mem42;
        };
    };

    union {
        int mem43;
        struct {
            int mem44;
        };
        struct {
            int mem45;
        } internA;
        struct i49 {
            int mem46;
        };
        struct i49 mem47;
        struct i50 {
            int mem48;
        } internB;
        struct i51 {
            int mem49;
        };
    } member4;

    union iud {
        int mem50;
        struct {
            int mem51;
        };
        struct {
            int mem52;
        } internA;
        struct i52 {
            int mem53;
        };
        struct i52 mem54;
        struct i53 {
            int mem55;
        } internB;
        struct i54 {
            int mem56;
        };
    };
    union iua member5;

    union iue {
        int mem57;
        struct {
            int mem58;
        };
        struct {
            int mem59;
        } internA;
        struct i55 {
            int mem60;
        };
        struct i55 mem61;
        struct i56 {
            int mem62;
        } internB;
        struct i57 {
            int mem63;
        };
    } member6;

    union iuf { // unreachable
        int mem64;
        struct {
            int mem65;
        };
        struct {
            int mem66;
        } internA;
        struct i58 {
            int mem67;
        };
        struct i58 mem68;
        struct i59 {
            int mem69;
        } internB;
        struct i60 {
            int mem70;
        };
    };
};

/******************************************************************************
 * Capitalization
 ******************************************************************************/

typedef struct cap_s {
    int member;
    int Member;
};

typedef struct cap_S {
    int member;
    int Member;
};

typedef union cap_u {
    int member;
    int Member;
};

typedef union cap_U {
    int member;
    int Member;
};

/******************************************************************************
 *
 ******************************************************************************/

int main(int argc, char const *argv[])
{
    struct s mystruct;
    union u myunion;
    struct cap_s c1;
    struct cap_S c2;
    union cap_u u1;
    union cap_U u2;

    /*
     * This section is meant for manual testing.
     * Please do not change unless required for an automated regression.
     */

    return 0;
}
