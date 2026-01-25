//! # Numeric Trait Implementations for `AADVar`
//!
//! This module implements traits from the `num_traits` crate, most importantly the
//! `Float` trait. This allows `AADVar` to be used as a generic type parameter
//! in functions that expect a floating-point number (i.e., `<T: Float>`),
//! making the AAD functionality seamlessly integrate with generic numeric code.

use super::AADVar;
use crate::tape::push_to_tape;
use num_traits::{Float, Num, NumCast, One, ToPrimitive, Zero};

// `Num` and `NumCast` are required by the `Float` trait.
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

/// Implements `Zero` for `AADVar`, allowing the creation of an additive identity.
impl Zero for AADVar {
    /// Returns an `AADVar` with a value of 0.0, registered as a constant on the tape.
    fn zero() -> Self {
        AADVar::constant(0.0)
    }

    /// Checks if the `AADVar`'s value is zero.
    fn is_zero(&self) -> bool {
        self.value.is_zero()
    }
}

/// Implements `One` for `AADVar`, allowing the creation of a multiplicative identity.
impl One for AADVar {
    /// Returns an `AADVar` with a value of 1.0, registered as a constant on the tape.
    fn one() -> Self {
        AADVar::constant(1.0)
    }
}

/// Implements the `Float` trait, providing a wide range of mathematical functions.
///
/// Each function is implemented to not only compute the value but also to push the
/// correct derivative (weight) onto the AAD tape, enabling the reverse-mode
/// differentiation.
impl Float for AADVar {
    // --- Constants and Special Values ---
    // These just create new constants on the tape.
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

    // --- Classification ---
    // These methods just inspect the value and don't affect the tape.
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

    // --- Rounding Functions ---
    // The derivatives of these functions are zero almost everywhere, so for simplicity,
    // we treat them as constants, effectively stopping the gradient flow.
    fn floor(self) -> Self {
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

    // --- Core Mathematical Functions ---

    /// Computes the absolute value. The derivative is `signum(x)`, or `1` if `x>=0` and `-1` if `x<0`.
    fn abs(self) -> Self {
        let sign = if self.value >= 0.0 { 1.0 } else { -1.0 };
        let new_index = push_to_tape(vec![sign], vec![self.index]);
        AADVar {
            value: self.value.abs(),
            index: new_index,
        }
    }

    /// Returns the sign of the number. This is treated as a constant.
    fn signum(self) -> Self {
        AADVar::constant(self.value.signum())
    }

    fn is_sign_positive(self) -> bool {
        self.value.is_sign_positive()
    }

    fn is_sign_negative(self) -> bool {
        self.value.is_sign_negative()
    }

    /// Fused multiply-add. Decomposes into `self * a + b`.
    fn mul_add(self, a: Self, b: Self) -> Self {
        self * a + b
    }

    /// Computes the reciprocal (1/x). The derivative is `-1/x^2`, which is `-recip(x)^2`.
    fn recip(self) -> Self {
        let res = self.value.recip();
        let new_index = push_to_tape(vec![-res * res], vec![self.index]);
        AADVar {
            value: res,
            index: new_index,
        }
    }

    /// Raises a number to an integer power. d/dx(x^n) = n*x^(n-1).
    fn powi(self, n: i32) -> Self {
        let res = self.value.powi(n);
        let deriv = (n as f64) * self.value.powi(n - 1);
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar {
            value: res,
            index: new_index,
        }
    }

    /// Raises a number to a floating point power. For `z = x^n`:
    /// - `dz/dx = n * x^(n-1)`
    /// - `dz/dn = x^n * ln(x)`
    fn powf(self, n: Self) -> Self {
        let res = self.value.powf(n.value);
        let d_base = n.value * self.value.powf(n.value - 1.0);
        let d_exp = res * self.value.ln();

        let new_index = push_to_tape(vec![d_base, d_exp], vec![self.index, n.index]);
        AADVar {
            value: res,
            index: new_index,
        }
    }

    /// Computes the square root. d/dx(sqrt(x)) = 1 / (2*sqrt(x)).
    fn sqrt(self) -> Self {
        let res = self.value.sqrt();
        let new_index = push_to_tape(vec![0.5 / res], vec![self.index]);
        AADVar {
            value: res,
            index: new_index,
        }
    }

    /// Computes the exponential function. d/dx(e^x) = e^x.
    fn exp(self) -> Self {
        let res = self.value.exp();
        let new_index = push_to_tape(vec![res], vec![self.index]);
        AADVar {
            value: res,
            index: new_index,
        }
    }

    /// Computes `2^x`. d/dx(2^x) = 2^x * ln(2).
    fn exp2(self) -> Self {
        let res = self.value.exp2();
        let deriv = res * std::f64::consts::LN_2;
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar {
            value: res,
            index: new_index,
        }
    }

    /// Computes the natural logarithm. d/dx(ln(x)) = 1/x.
    fn ln(self) -> Self {
        let res = self.value.ln();
        let new_index = push_to_tape(vec![1.0 / self.value], vec![self.index]);
        AADVar {
            value: res,
            index: new_index,
        }
    }

    /// Computes the logarithm with a given base. Decomposes to `ln(self) / ln(base)`.
    fn log(self, base: Self) -> Self {
        self.ln() / base.ln()
    }

    /// Computes the base-2 logarithm. d/dx(log2(x)) = 1 / (x * ln(2)).
    fn log2(self) -> Self {
        let res = self.value.log2();
        let deriv = 1.0 / (self.value * std::f64::consts::LN_2);
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar {
            value: res,
            index: new_index,
        }
    }

    /// Computes the base-10 logarithm. d/dx(log10(x)) = 1 / (x * ln(10)).
    fn log10(self) -> Self {
        let res = self.value.log10();
        let deriv = 1.0 / (self.value * std::f64::consts::LN_10);
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar {
            value: res,
            index: new_index,
        }
    }

    /// Returns the maximum of two numbers. The derivative is 1 for the maximum value and 0 for the other.
    fn max(self, other: Self) -> Self {
        if self.value >= other.value {
            // `self` is the max, so the derivative with respect to `self` is 1.
            let new_index = push_to_tape(vec![1.0], vec![self.index]);
            AADVar {
                value: self.value,
                index: new_index,
            }
        } else {
            // `other` is the max, so the derivative with respect to `other` is 1.
            let new_index = push_to_tape(vec![1.0], vec![other.index]);
            AADVar {
                value: other.value,
                index: new_index,
            }
        }
    }

    /// Returns the minimum of two numbers. The derivative is 1 for the minimum value and 0 for the other.
    fn min(self, other: Self) -> Self {
        if self.value <= other.value {
            let new_index = push_to_tape(vec![1.0], vec![self.index]);
            AADVar {
                value: self.value,
                index: new_index,
            }
        } else {
            let new_index = push_to_tape(vec![1.0], vec![other.index]);
            AADVar {
                value: other.value,
                index: new_index,
            }
        }
    }

    /// Absolute difference. Decomposes to `(self - other).abs()` if `self > other`, else `0`.
    fn abs_sub(self, other: Self) -> Self {
        if self.value <= other.value {
            AADVar::constant(0.0)
        } else {
            self - other
        }
    }

    /// Computes the cube root. d/dx(x^(1/3)) = 1 / (3 * x^(2/3)).
    fn cbrt(self) -> Self {
        let res = self.value.cbrt();
        let deriv = 1.0 / (3.0 * res * res);
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar {
            value: res,
            index: new_index,
        }
    }

    /// Computes the hypotenuse. For `h = sqrt(x^2 + y^2)`:
    /// - `dh/dx = x / h`
    /// - `dh/dy = y / h`
    fn hypot(self, other: Self) -> Self {
        let res = self.value.hypot(other.value);
        let d_self = self.value / res;
        let d_other = other.value / res;
        let new_index = push_to_tape(vec![d_self, d_other], vec![self.index, other.index]);
        AADVar {
            value: res,
            index: new_index,
        }
    }

    /// Computes the sine. d/dx(sin(x)) = cos(x).
    fn sin(self) -> Self {
        let res = self.value.sin();
        let deriv = self.value.cos();
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar {
            value: res,
            index: new_index,
        }
    }

    /// Computes the cosine. d/dx(cos(x)) = -sin(x).
    fn cos(self) -> Self {
        let res = self.value.cos();
        let deriv = -self.value.sin();
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar {
            value: res,
            index: new_index,
        }
    }

    /// Computes the tangent. d/dx(tan(x)) = sec^2(x) = 1 + tan^2(x).
    fn tan(self) -> Self {
        let res = self.value.tan();
        let deriv = 1.0 + res * res;
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar {
            value: res,
            index: new_index,
        }
    }

    /// Computes the arcsine. d/dx(asin(x)) = 1 / sqrt(1 - x^2).
    fn asin(self) -> Self {
        let res = self.value.asin();
        let deriv = 1.0 / (1.0 - self.value * self.value).sqrt();
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar {
            value: res,
            index: new_index,
        }
    }

    /// Computes the arccosine. d/dx(acos(x)) = -1 / sqrt(1 - x^2).
    fn acos(self) -> Self {
        let res = self.value.acos();
        let deriv = -1.0 / (1.0 - self.value * self.value).sqrt();
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar {
            value: res,
            index: new_index,
        }
    }

    /// Computes the arctangent. d/dx(atan(x)) = 1 / (1 + x^2).
    fn atan(self) -> Self {
        let res = self.value.atan();
        let deriv = 1.0 / (1.0 + self.value * self.value);
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar {
            value: res,
            index: new_index,
        }
    }

    /// Computes the four-quadrant arctangent. For `z = atan2(y, x)`:
    /// - `dz/dy = x / (x^2 + y^2)`
    /// - `dz/dx = -y / (x^2 + y^2)`
    fn atan2(self, other: Self) -> Self {
        let res = self.value.atan2(other.value);
        let denom = self.value * self.value + other.value * other.value;
        let d_self = other.value / denom; // Corresponds to y
        let d_other = -self.value / denom; // Corresponds to x
        let new_index = push_to_tape(vec![d_self, d_other], vec![self.index, other.index]);
        AADVar {
            value: res,
            index: new_index,
        }
    }

    /// Simultaneously computes sine and cosine. Decomposes into individual calls.
    fn sin_cos(self) -> (Self, Self) {
        (self.sin(), self.cos())
    }

    /// Computes `e^x - 1`. d/dx = e^x.
    fn exp_m1(self) -> Self {
        let res = self.value.exp_m1();
        let deriv = res + 1.0; // This is e^x
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar {
            value: res,
            index: new_index,
        }
    }

    /// Computes `ln(1+x)`. d/dx = 1 / (1+x).
    fn ln_1p(self) -> Self {
        let res = self.value.ln_1p();
        let deriv = 1.0 / (1.0 + self.value);
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar {
            value: res,
            index: new_index,
        }
    }

    /// Computes the hyperbolic sine. d/dx(sinh(x)) = cosh(x).
    fn sinh(self) -> Self {
        let res = self.value.sinh();
        let deriv = self.value.cosh();
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar {
            value: res,
            index: new_index,
        }
    }

    /// Computes the hyperbolic cosine. d/dx(cosh(x)) = sinh(x).
    fn cosh(self) -> Self {
        let res = self.value.cosh();
        let deriv = self.value.sinh();
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar {
            value: res,
            index: new_index,
        }
    }

    /// Computes the hyperbolic tangent. d/dx(tanh(x)) = 1 - tanh^2(x).
    fn tanh(self) -> Self {
        let res = self.value.tanh();
        let deriv = 1.0 - res * res;
        let new_index = push_to_tape(vec![deriv], vec![self.index]);
        AADVar {
            value: res,
            index: new_index,
        }
    }
    
    // --- Inverse Hyperbolic Functions ---
    
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
