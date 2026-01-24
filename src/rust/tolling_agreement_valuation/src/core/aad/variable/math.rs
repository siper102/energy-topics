use num_traits::{Float, Num, NumCast, One, ToPrimitive, Zero};
use crate::core::aad::tape::push_to_tape;
use super::AADVar;

impl Num for AADVar {
    type FromStrRadixErr = num_traits::ParseFloatError;

    fn from_str_radix(str: &str, radix: u32) -> Result<Self, Self::FromStrRadixErr> {
        f64::from_str_radix(str, radix).map(AADVar::constant)
    }
}

impl NumCast for AADVar {
    fn from<T: ToPrimitive>(n: T) -> Option<Self> {
        n.to_f64().map(AADVar::constant)
    }
}

impl Zero for AADVar {
    fn zero() -> Self {
        AADVar::constant(0.0)
    }

    fn is_zero(&self) -> bool {
        self.value.is_zero()
    }
}

impl One for AADVar {
    fn one() -> Self {
        AADVar::constant(1.0)
    }
}

impl Float for AADVar {
    fn nan() -> Self {
        AADVar::constant(f64::nan())
    }

    fn infinity() -> Self {
        AADVar::constant(f64::infinity())
    }

    fn neg_infinity() -> Self {
        AADVar::constant(f64::neg_infinity())
    }

    fn neg_zero() -> Self {
        AADVar::constant(f64::neg_zero())
    }

    fn min_value() -> Self {
        AADVar::constant(f64::min_value())
    }

    fn min_positive_value() -> Self {
        AADVar::constant(f64::min_positive_value())
    }

    fn max_value() -> Self {
        AADVar::constant(f64::max_value())
    }

    fn is_nan(self) -> bool {
        self.value.is_nan()
    }

    fn is_infinite(self) -> bool {
        self.value.is_infinite()
    }

    fn is_finite(self) -> bool {
        self.value.is_finite()
    }

    fn is_normal(self) -> bool {
        self.value.is_normal()
    }

    fn classify(self) -> std::num::FpCategory {
        self.value.classify()
    }

    fn floor(self) -> Self {
        // Derivative is 0 almost everywhere, usually ignored or treated as const
        AADVar::constant(self.value.floor())
    }

    fn ceil(self) -> Self {
        AADVar::constant(self.value.ceil())
    }

    fn round(self) -> Self {
        AADVar::constant(self.value.round())
    }

    fn trunc(self) -> Self {
        AADVar::constant(self.value.trunc())
    }

    fn fract(self) -> Self {
        AADVar::constant(self.value.fract())
    }

    fn abs(self) -> Self {
        let sign = if self.value >= 0.0 { 1.0 } else { -1.0 };
        let new_index = push_to_tape(vec![sign], vec![self.index]);
        AADVar { value: self.value.abs(), index: new_index }
    }

    fn signum(self) -> Self {
        AADVar::constant(self.value.signum())
    }

    fn is_sign_positive(self) -> bool {
        self.value.is_sign_positive()
    }

    fn is_sign_negative(self) -> bool {
        self.value.is_sign_negative()
    }

    fn mul_add(self, a: Self, b: Self) -> Self {
        self * a + b
    }

    fn recip(self) -> Self {
        let res = self.value.recip();
        let new_index = push_to_tape(vec![-res * res], vec![self.index]);
        AADVar { value: res, index: new_index }
    }

    fn powi(self, n: i32) -> Self {
        let res = self.value.powi(n);
        let deriv = (n as f64) * self.value.powi(n - 1);
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar { value: res, index: new_index }
    }

    fn powf(self, n: Self) -> Self {
        let res = self.value.powf(n.value);
        // d/dx (x^n) = n * x^(n-1)
        // d/dn (x^n) = x^n * ln(x)
        let d_base = n.value * self.value.powf(n.value - 1.0);
        let d_exp = res * self.value.ln();
        
        let new_index = push_to_tape(vec![d_base, d_exp], vec![self.index, n.index]);
        AADVar { value: res, index: new_index }
    }

    fn sqrt(self) -> Self {
        let res = self.value.sqrt();
        let new_index = push_to_tape(vec![0.5 / res], vec![self.index]);
        AADVar { value: res, index: new_index }
    }

    fn exp(self) -> Self {
        let res = self.value.exp();
        let new_index = push_to_tape(vec![res], vec![self.index]);
        AADVar { value: res, index: new_index }
    }

    fn exp2(self) -> Self {
        let res = self.value.exp2();
        let deriv = res * std::f64::consts::LN_2;
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar { value: res, index: new_index }
    }

    fn ln(self) -> Self {
        let res = self.value.ln();
        let new_index = push_to_tape(vec![1.0 / self.value], vec![self.index]);
        AADVar { value: res, index: new_index }
    }

    fn log(self, base: Self) -> Self {
        self.ln() / base.ln()
    }

    fn log2(self) -> Self {
        let res = self.value.log2();
        let deriv = 1.0 / (self.value * std::f64::consts::LN_2);
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar { value: res, index: new_index }
    }

    fn log10(self) -> Self {
        let res = self.value.log10();
        let deriv = 1.0 / (self.value * std::f64::consts::LN_10);
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar { value: res, index: new_index }
    }

    fn max(self, other: Self) -> Self {
        if self.value >= other.value {
            let new_index = push_to_tape(vec![1.0], vec![self.index]);
            AADVar { value: self.value, index: new_index }
        } else {
            let new_index = push_to_tape(vec![1.0], vec![other.index]);
            AADVar { value: other.value, index: new_index }
        }
    }

    fn min(self, other: Self) -> Self {
        if self.value <= other.value {
            let new_index = push_to_tape(vec![1.0], vec![self.index]);
            AADVar { value: self.value, index: new_index }
        } else {
            let new_index = push_to_tape(vec![1.0], vec![other.index]);
            AADVar { value: other.value, index: new_index }
        }
    }

    fn abs_sub(self, other: Self) -> Self {
        if self.value <= other.value {
             AADVar::constant(0.0)
        } else {
            self - other
        }
    }

    fn cbrt(self) -> Self {
        let res = self.value.cbrt();
        let deriv = 1.0 / (3.0 * res * res);
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar { value: res, index: new_index }
    }

    fn hypot(self, other: Self) -> Self {
        let res = self.value.hypot(other.value);
        let d_self = self.value / res;
        let d_other = other.value / res;
        let new_index = push_to_tape(vec![d_self, d_other], vec![self.index, other.index]);
        AADVar { value: res, index: new_index }
    }

    fn sin(self) -> Self {
        let res = self.value.sin();
        let deriv = self.value.cos();
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar { value: res, index: new_index }
    }

    fn cos(self) -> Self {
        let res = self.value.cos();
        let deriv = -self.value.sin();
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar { value: res, index: new_index }
    }

    fn tan(self) -> Self {
        let res = self.value.tan();
        let deriv = 1.0 + res * res;
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar { value: res, index: new_index }
    }

    fn asin(self) -> Self {
        let res = self.value.asin();
        let deriv = 1.0 / (1.0 - self.value * self.value).sqrt();
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar { value: res, index: new_index }
    }

    fn acos(self) -> Self {
        let res = self.value.acos();
        let deriv = -1.0 / (1.0 - self.value * self.value).sqrt();
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar { value: res, index: new_index }
    }

    fn atan(self) -> Self {
        let res = self.value.atan();
        let deriv = 1.0 / (1.0 + self.value * self.value);
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar { value: res, index: new_index }
    }

    fn atan2(self, other: Self) -> Self {
         let res = self.value.atan2(other.value);
         let denom = self.value * self.value + other.value * other.value;
         let d_self = other.value / denom;
         let d_other = -self.value / denom;
         let new_index = push_to_tape(vec![d_self, d_other], vec![self.index, other.index]);
         AADVar { value: res, index: new_index }
    }

    fn sin_cos(self) -> (Self, Self) {
        (self.sin(), self.cos())
    }

    fn exp_m1(self) -> Self {
         let res = self.value.exp_m1();
         let deriv = res + 1.0;
         let new_index = push_to_tape(vec![deriv], vec![self.index]);
         AADVar { value: res, index: new_index }
    }

    fn ln_1p(self) -> Self {
        let res = self.value.ln_1p();
        let deriv = 1.0 / (1.0 + self.value);
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar { value: res, index: new_index }
    }

    fn sinh(self) -> Self {
        let res = self.value.sinh();
        let deriv = self.value.cosh();
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar { value: res, index: new_index }
    }

    fn cosh(self) -> Self {
        let res = self.value.cosh();
        let deriv = self.value.sinh();
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar { value: res, index: new_index }
    }

    fn tanh(self) -> Self {
        let res = self.value.tanh();
        let deriv = 1.0 - res * res;
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar { value: res, index: new_index }
    }

    fn asinh(self) -> Self {
        let res = self.value.asinh();
        let deriv = 1.0 / (self.value * self.value + 1.0).sqrt();
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar { value: res, index: new_index }
    }

    fn acosh(self) -> Self {
        let res = self.value.acosh();
        let deriv = 1.0 / (self.value * self.value - 1.0).sqrt();
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar { value: res, index: new_index }
    }

    fn atanh(self) -> Self {
        let res = self.value.atanh();
        let deriv = 1.0 / (1.0 - self.value * self.value);
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar { value: res, index: new_index }
    }

    fn integer_decode(self) -> (u64, i16, i8) {
        self.value.integer_decode()
    }
}
