pub mod tape;
pub mod variable;

pub use tape::{backward, clear_tape, get_tape_len};
pub use variable::AADVar;
