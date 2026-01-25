use std::cell::RefCell;

thread_local! {
    /// The global, thread-local computation graph, also known as the "tape".
    ///
    /// This static variable holds the sequence of all operations performed on `AADVar`s
    /// within a single thread. Using `thread_local!` ensures that each thread gets its
    /// own independent tape, making the AAD process thread-safe for parallel computations.
    ///
    /// `RefCell` is used to allow for "interior mutability". It lets us borrow a mutable
    /// reference to the `Tape` from an immutable context, which is necessary because
    /// `TAPE` is a `static` variable.
    pub static TAPE: RefCell<Tape> = RefCell::new(Tape::new());
}

/// Represents the sequence of operations in the computation graph.
pub struct Tape {
    /// A vector of `Node`s, where each node represents a single operation
    /// (like addition or multiplication) and its relationship to its inputs.
    pub nodes: Vec<Node>,
}

impl Tape {
    /// Creates a new, empty `Tape`.
    pub fn new() -> Self {
        Tape {
            // Pre-allocate capacity to reduce re-allocations during computation.
            nodes: Vec::with_capacity(10000),
        }
    }

    /// Adds a new `Node` to the tape and returns its index.
    ///
    /// This index is what links an `AADVar` to its corresponding operation on the tape.
    pub fn push(&mut self, node: Node) -> usize {
        let idx = self.nodes.len();
        self.nodes.push(node);
        idx
    }

    /// Clears all nodes from the tape, preparing it for a new computation.
    pub fn clear(&mut self) {
        self.nodes.clear();
    }

    /// Executes the backward pass of the automatic differentiation.
    ///
    /// This method traverses the tape in reverse order, applying the chain rule at each
    /// node to propagate the derivatives from the output variable back to the inputs.
    ///
    /// # Arguments
    ///
    /// * `adjoints`: A mutable slice representing the derivatives `d(output)/d(node)`.
    ///   It must be the same length as the tape. Before calling, it should be
    ///   initialized to all zeros, except for a `1.0` at the index of the final
    ///   output variable.
    ///
    /// # Panics
    ///
    /// Panics if the length of `adjoints` does not match the number of nodes on the tape.
    pub fn execute_backward(&self, adjoints: &mut [f64]) {
        if adjoints.len() != self.nodes.len() {
            panic!(
                "Adjoints vector length {} does not match tape length {}",
                adjoints.len(),
                self.nodes.len()
            );
        }

        // Iterate backwards from the last recorded operation to the first.
        for i in (0..self.nodes.len()).rev() {
            let node = &self.nodes[i];
            let adj_i = adjoints[i];

            // Optimization: If the derivative of the output with respect to the current
            // node is zero, then this node does not contribute to the final result,
            // and we can skip propagating its derivatives further.
            if adj_i == 0.0 {
                continue;
            }

            // The core of the chain rule:
            // d(output)/d(parent) += d(output)/d(node) * d(node)/d(parent)
            // where `d(output)/d(node)` is `adj_i` and `d(node)/d(parent)` is `weight`.
            for (parent_idx, weight) in node.parents.iter().zip(node.weights.iter()) {
                adjoints[*parent_idx] += adj_i * weight;
            }
        }
    }
}

/// Represents a single operation (or a variable) in the computation graph.
pub struct Node {
    /// The partial derivatives of this node with respect to its parents.
    /// For an operation `z = f(x, y)`, the weights would be `[dz/dx, dz/dy]`.
    pub weights: Vec<f64>,
    /// The indices on the tape of the parent nodes (i.e., the inputs to the operation).
    pub parents: Vec<usize>,
}

/// A helper function to push a new node to the thread-local tape.
///
/// This provides a safe, public interface for modifying the global `TAPE`.
pub fn push_to_tape(weights: Vec<f64>, parents: Vec<usize>) -> usize {
    TAPE.with(|tape_cell| {
        let mut tape = tape_cell.borrow_mut();
        tape.push(Node { weights, parents })
    })
}

/// A helper function to clear the thread-local tape.
pub fn clear_tape() {
    TAPE.with(|tape_cell| {
        tape_cell.borrow_mut().clear();
    })
}

/// A helper function to get the current number of nodes on the thread-local tape.
/// This is used to correctly size the `adjoints` vector before the backward pass.
pub fn get_tape_len() -> usize {
    TAPE.with(|tape_cell| tape_cell.borrow().nodes.len())
}

/// A helper function to execute the backward pass on the thread-local tape.
pub fn backward(adjoints: &mut [f64]) {
    TAPE.with(|tape_cell| {
        tape_cell.borrow().execute_backward(adjoints);
    })
}
