// Filename: weakPointerCallback.h
// Created by:  drose (06Oct06)
//
////////////////////////////////////////////////////////////////////
//
// PANDA 3D SOFTWARE
// Copyright (c) Carnegie Mellon University.  All rights reserved.
//
// All use of this software is subject to the terms of the revised BSD
// license.  You should have received a copy of this license along
// with this source code in a file named "LICENSE."
//
////////////////////////////////////////////////////////////////////

#ifndef WEAKPOINTERCALLBACK_H
#define WEAKPOINTERCALLBACK_H

#include "pandabase.h"

////////////////////////////////////////////////////////////////////
//       Class : WeakPointerCallback
// Description : Derive from this class and override the callback()
//               method if you want to get an immediate callback from
//               a WeakPointerTo object when its referenced pointer is
//               deleted.
////////////////////////////////////////////////////////////////////
class EXPCL_PANDAEXPRESS WeakPointerCallback {
public:
  virtual ~WeakPointerCallback();
  virtual void wp_callback(void *pointer)=0;
};

#include "weakPointerCallback.I"

#endif
